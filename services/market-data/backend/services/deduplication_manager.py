
import hashlib
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from models.trade_model import UniversalTradeDataModel, TradeRecord
from logging_manager import log_info, log_warning, log_error, LogCategory

class DuplicateMatchType(Enum):
    EXACT = "exact"
    FUZZY_TIME = "fuzzy_time"
    FUZZY_PRICE = "fuzzy_price"
    COMPOSITE = "composite"

@dataclass
class DuplicateMatch:
    """Represents a potential duplicate trade match."""
    existing_trade_id: str
    new_trade_data: Dict[str, Any]
    match_type: DuplicateMatchType
    confidence_score: float
    matching_fields: List[str]
    differences: Dict[str, Tuple[Any, Any]]

class TradeDeduplicationManager:
    """Advanced trade deduplication with multiple matching strategies."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.init_dedup_tables()
        
        # Fuzzy matching tolerances
        self.time_tolerance_minutes = 5
        self.price_tolerance_percent = 0.01  # 1%
        self.minimum_confidence_score = 0.85
    
    def init_dedup_tables(self):
        """Initialize deduplication tracking tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trade fingerprints table for fast duplicate detection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                exact_hash TEXT NOT NULL,
                fuzzy_hash TEXT NOT NULL,
                symbol TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                qty REAL NOT NULL,
                direction TEXT NOT NULL,
                data_source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Duplicate resolution log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicate_resolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_trade_id TEXT NOT NULL,
                duplicate_trade_hash TEXT NOT NULL,
                match_type TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                action_taken TEXT NOT NULL,
                resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprints_exact_hash ON trade_fingerprints (exact_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprints_fuzzy_hash ON trade_fingerprints (fuzzy_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprints_user_symbol ON trade_fingerprints (user_id, symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprints_time_range ON trade_fingerprints (entry_time, exit_time)')
        
        conn.commit()
        conn.close()
    
    def generate_exact_hash(self, trade_data: Dict[str, Any]) -> str:
        """Generate exact hash for precise duplicate detection."""
        # Use only the most critical fields that should be identical
        key_fields = [
            str(trade_data.get('symbol', '')).upper(),
            str(trade_data.get('entry_time', '')),
            str(trade_data.get('exit_time', '')),
            f"{float(trade_data.get('entry_price', 0)):.6f}",
            f"{float(trade_data.get('exit_price', 0)):.6f}",
            f"{float(trade_data.get('qty', 0)):.6f}",
            str(trade_data.get('direction', '')).lower()
        ]
        
        hash_string = '|'.join(key_fields)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def generate_fuzzy_hash(self, trade_data: Dict[str, Any]) -> str:
        """Generate fuzzy hash for near-duplicate detection."""
        # Use rounded values and normalized times for fuzzy matching
        try:
            entry_time = pd.to_datetime(trade_data.get('entry_time'))
            exit_time = pd.to_datetime(trade_data.get('exit_time'))
            
            # Round to nearest 5-minute interval for time fuzzing
            entry_rounded = entry_time.round('5min')
            exit_rounded = exit_time.round('5min')
            
            # Round prices to 2 decimal places
            entry_price = round(float(trade_data.get('entry_price', 0)), 2)
            exit_price = round(float(trade_data.get('exit_price', 0)), 2)
            qty = round(float(trade_data.get('qty', 0)), 2)
            
            fuzzy_fields = [
                str(trade_data.get('symbol', '')).upper(),
                entry_rounded.strftime('%Y-%m-%d %H:%M'),
                exit_rounded.strftime('%Y-%m-%d %H:%M'),
                f"{entry_price:.2f}",
                f"{exit_price:.2f}",
                f"{qty:.2f}",
                str(trade_data.get('direction', '')).lower()
            ]
            
            hash_string = '|'.join(fuzzy_fields)
            return hashlib.sha256(hash_string.encode()).hexdigest()
            
        except Exception as e:
            log_error(f"Error generating fuzzy hash: {str(e)}", category=LogCategory.DATA_PROCESSING)
            return self.generate_exact_hash(trade_data)
    
    def find_potential_duplicates(self, trade_data: Dict[str, Any], user_id: int) -> List[DuplicateMatch]:
        """Find potential duplicate trades using multiple matching strategies."""
        potential_duplicates = []
        
        exact_hash = self.generate_exact_hash(trade_data)
        fuzzy_hash = self.generate_fuzzy_hash(trade_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Exact hash match (highest confidence)
        cursor.execute('''
            SELECT trade_id, symbol, entry_time, exit_time, entry_price, exit_price, qty, direction, data_source
            FROM trade_fingerprints 
            WHERE user_id = ? AND exact_hash = ?
        ''', (user_id, exact_hash))
        
        exact_matches = cursor.fetchall()
        for match in exact_matches:
            potential_duplicates.append(DuplicateMatch(
                existing_trade_id=match[0],
                new_trade_data=trade_data,
                match_type=DuplicateMatchType.EXACT,
                confidence_score=1.0,
                matching_fields=['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'qty', 'direction'],
                differences={}
            ))
        
        # 2. Fuzzy hash match (high confidence)
        if not exact_matches:  # Only check fuzzy if no exact matches
            cursor.execute('''
                SELECT trade_id, symbol, entry_time, exit_time, entry_price, exit_price, qty, direction, data_source
                FROM trade_fingerprints 
                WHERE user_id = ? AND fuzzy_hash = ? AND exact_hash != ?
            ''', (user_id, fuzzy_hash, exact_hash))
            
            fuzzy_matches = cursor.fetchall()
            for match in fuzzy_matches:
                potential_duplicates.append(DuplicateMatch(
                    existing_trade_id=match[0],
                    new_trade_data=trade_data,
                    match_type=DuplicateMatchType.FUZZY_TIME,
                    confidence_score=0.95,
                    matching_fields=['symbol', 'direction', 'entry_time_fuzzy', 'exit_time_fuzzy'],
                    differences=self._calculate_differences(match, trade_data)
                ))
        
        # 3. Symbol + time range + similar prices (medium confidence)
        if not potential_duplicates:
            symbol = trade_data.get('symbol', '').upper()
            entry_time = pd.to_datetime(trade_data.get('entry_time'))
            exit_time = pd.to_datetime(trade_data.get('exit_time'))
            
            # Search within time tolerance
            time_start = entry_time - timedelta(minutes=self.time_tolerance_minutes)
            time_end = entry_time + timedelta(minutes=self.time_tolerance_minutes)
            
            cursor.execute('''
                SELECT trade_id, symbol, entry_time, exit_time, entry_price, exit_price, qty, direction, data_source
                FROM trade_fingerprints 
                WHERE user_id = ? AND symbol = ? 
                AND entry_time BETWEEN ? AND ?
                AND direction = ?
            ''', (user_id, symbol, time_start, time_end, trade_data.get('direction', '').lower()))
            
            time_matches = cursor.fetchall()
            for match in time_matches:
                confidence = self._calculate_price_similarity_confidence(match, trade_data)
                if confidence >= self.minimum_confidence_score:
                    potential_duplicates.append(DuplicateMatch(
                        existing_trade_id=match[0],
                        new_trade_data=trade_data,
                        match_type=DuplicateMatchType.FUZZY_PRICE,
                        confidence_score=confidence,
                        matching_fields=['symbol', 'direction', 'time_range'],
                        differences=self._calculate_differences(match, trade_data)
                    ))
        
        conn.close()
        
        # Sort by confidence score (highest first)
        potential_duplicates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return potential_duplicates
    
    def _calculate_differences(self, existing_match: Tuple, new_trade_data: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
        """Calculate differences between existing and new trade."""
        differences = {}
        
        field_mapping = {
            1: 'symbol',
            2: 'entry_time', 
            3: 'exit_time',
            4: 'entry_price',
            5: 'exit_price',
            6: 'qty',
            7: 'direction',
            8: 'data_source'
        }
        
        for idx, field in field_mapping.items():
            if idx < len(existing_match):
                existing_value = existing_match[idx]
                new_value = new_trade_data.get(field)
                
                if str(existing_value) != str(new_value):
                    differences[field] = (existing_value, new_value)
        
        return differences
    
    def _calculate_price_similarity_confidence(self, existing_match: Tuple, new_trade_data: Dict[str, Any]) -> float:
        """Calculate confidence based on price similarity."""
        try:
            existing_entry_price = float(existing_match[4])
            existing_exit_price = float(existing_match[5])
            existing_qty = float(existing_match[6])
            
            new_entry_price = float(new_trade_data.get('entry_price', 0))
            new_exit_price = float(new_trade_data.get('exit_price', 0))
            new_qty = float(new_trade_data.get('qty', 0))
            
            # Calculate percentage differences
            entry_price_diff = abs(existing_entry_price - new_entry_price) / existing_entry_price
            exit_price_diff = abs(existing_exit_price - new_exit_price) / existing_exit_price
            qty_diff = abs(existing_qty - new_qty) / existing_qty
            
            # Average the differences
            avg_diff = (entry_price_diff + exit_price_diff + qty_diff) / 3
            
            # Convert to confidence score (lower difference = higher confidence)
            confidence = max(0.0, 1.0 - (avg_diff / self.price_tolerance_percent))
            
            return min(0.99, confidence)  # Cap at 0.99 for fuzzy matches
            
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def deduplicate_trades(self, trades_data: List[Dict[str, Any]], user_id: int, 
                          auto_resolve: bool = True) -> Dict[str, Any]:
        """Deduplicate a list of trades and return the results."""
        dedup_results = {
            'original_count': len(trades_data),
            'unique_trades': [],
            'duplicates_found': [],
            'duplicates_removed': 0,
            'conflicts_requiring_review': [],
            'processing_errors': []
        }
        
        processed_hashes = set()
        
        for trade_data in trades_data:
            try:
                # Generate hashes for this trade
                exact_hash = self.generate_exact_hash(trade_data)
                
                # Skip if we've already processed this exact trade in this batch
                if exact_hash in processed_hashes:
                    dedup_results['duplicates_removed'] += 1
                    dedup_results['duplicates_found'].append({
                        'trade_data': trade_data,
                        'reason': 'Duplicate within current batch',
                        'action': 'skipped'
                    })
                    continue
                
                # Find potential duplicates in existing data
                potential_duplicates = self.find_potential_duplicates(trade_data, user_id)
                
                if not potential_duplicates:
                    # No duplicates found - this is a unique trade
                    dedup_results['unique_trades'].append(trade_data)
                    processed_hashes.add(exact_hash)
                    
                elif auto_resolve and potential_duplicates[0].confidence_score >= 0.95:
                    # High confidence duplicate - auto-resolve
                    best_match = potential_duplicates[0]
                    dedup_results['duplicates_removed'] += 1
                    dedup_results['duplicates_found'].append({
                        'trade_data': trade_data,
                        'existing_trade_id': best_match.existing_trade_id,
                        'match_type': best_match.match_type.value,
                        'confidence': best_match.confidence_score,
                        'differences': best_match.differences,
                        'action': 'auto_removed'
                    })
                    
                    # Log the resolution
                    self._log_duplicate_resolution(
                        user_id, best_match.existing_trade_id, exact_hash,
                        best_match.match_type, best_match.confidence_score, 'auto_removed'
                    )
                    
                else:
                    # Potential duplicate requiring manual review
                    dedup_results['conflicts_requiring_review'].append({
                        'trade_data': trade_data,
                        'potential_matches': [
                            {
                                'existing_trade_id': match.existing_trade_id,
                                'match_type': match.match_type.value,
                                'confidence': match.confidence_score,
                                'differences': match.differences
                            }
                            for match in potential_duplicates[:3]  # Top 3 matches
                        ]
                    })
                    
                    # For now, include the trade but flag it
                    trade_data['_requires_dedup_review'] = True
                    dedup_results['unique_trades'].append(trade_data)
                    processed_hashes.add(exact_hash)
                
            except Exception as e:
                dedup_results['processing_errors'].append({
                    'trade_data': trade_data,
                    'error': str(e)
                })
                log_error(f"Error processing trade for deduplication: {str(e)}", 
                         category=LogCategory.DATA_PROCESSING)
        
        # Log summary
        log_info(f"Deduplication completed: {dedup_results['original_count']} -> {len(dedup_results['unique_trades'])} trades, "
                f"{dedup_results['duplicates_removed']} duplicates removed, "
                f"{len(dedup_results['conflicts_requiring_review'])} requiring review",
                details=dedup_results,
                category=LogCategory.DATA_PROCESSING)
        
        return dedup_results
    
    def register_trades(self, trades: List[TradeRecord], user_id: int) -> None:
        """Register trade fingerprints for future deduplication."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for trade in trades:
            trade_dict = trade.to_dict()
            exact_hash = self.generate_exact_hash(trade_dict)
            fuzzy_hash = self.generate_fuzzy_hash(trade_dict)
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO trade_fingerprints 
                    (trade_id, user_id, exact_hash, fuzzy_hash, symbol, entry_time, exit_time,
                     entry_price, exit_price, qty, direction, data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.trade_id, user_id, exact_hash, fuzzy_hash,
                    trade.symbol, trade.entry_time, trade.exit_time,
                    trade.entry_price, trade.exit_price, trade.qty,
                    trade.direction.value, trade.data_source
                ))
            except Exception as e:
                log_error(f"Error registering trade fingerprint: {str(e)}", 
                         category=LogCategory.DATA_PROCESSING)
        
        conn.commit()
        conn.close()
    
    def _log_duplicate_resolution(self, user_id: int, original_trade_id: str, 
                                 duplicate_hash: str, match_type: DuplicateMatchType,
                                 confidence: float, action: str) -> None:
        """Log duplicate resolution for audit trail."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO duplicate_resolutions 
                (user_id, original_trade_id, duplicate_trade_hash, match_type,
                 confidence_score, action_taken)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, original_trade_id, duplicate_hash, match_type.value, confidence, action))
            
            conn.commit()
        except Exception as e:
            log_error(f"Error logging duplicate resolution: {str(e)}", 
                     category=LogCategory.DATA_PROCESSING)
        finally:
            conn.close()
    
    def get_deduplication_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get deduplication statistics for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get resolution stats
        cursor.execute('''
            SELECT match_type, action_taken, COUNT(*) as count, AVG(confidence_score) as avg_confidence
            FROM duplicate_resolutions 
            WHERE user_id = ? AND resolved_at >= ?
            GROUP BY match_type, action_taken
        ''', (user_id, cutoff_date))
        
        resolution_stats = cursor.fetchall()
        
        # Get total registered trades
        cursor.execute('''
            SELECT COUNT(*) FROM trade_fingerprints WHERE user_id = ?
        ''', (user_id,))
        
        total_trades = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_registered_trades': total_trades,
            'resolution_stats': [
                {
                    'match_type': row[0],
                    'action': row[1],
                    'count': row[2],
                    'avg_confidence': round(row[3], 3)
                }
                for row in resolution_stats
            ],
            'period_days': days
        }
    
    def cleanup_old_fingerprints(self, days_to_keep: int = 365) -> int:
        """Clean up old trade fingerprints to maintain performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cursor.execute('''
            DELETE FROM trade_fingerprints 
            WHERE created_at < ?
        ''', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        
        cursor.execute('''
            DELETE FROM duplicate_resolutions 
            WHERE resolved_at < ?
        ''', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        log_info(f"Cleaned up {deleted_count} old trade fingerprints", 
                category=LogCategory.SYSTEM)
        
        return deleted_count

# Global deduplication manager instance
dedup_manager = TradeDeduplicationManager()
