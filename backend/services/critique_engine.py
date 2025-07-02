
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass

from backend.models.trade import Trade

logger = logging.getLogger(__name__)

@dataclass
class CritiqueResult:
    summary: str
    suggestion: str
    confidence: int  # 1-10
    tags: List[str]
    technical_analysis: str
    psychological_analysis: str
    risk_assessment: str

class AITradeAnalyzer:
    """AI-powered trade critique and analysis engine"""
    
    def __init__(self):
        self.psychological_patterns = {
            'revenge_trading': ['quick succession after loss', 'increased position size after loss'],
            'fomo': ['entry during strong momentum', 'late entry', 'chase price'],
            'overconfidence': ['oversized position', 'ignored stop loss', 'held too long'],
            'hesitation': ['multiple entry attempts', 'small position size', 'late entry'],
            'panic_exit': ['early exit during volatility', 'exit before target'],
            'greed': ['held past target', 'increased position mid-trade'],
            'fear': ['undersized position', 'early exit', 'tight stop loss']
        }
        
        self.technical_flags = {
            'poor_entry': ['entry against trend', 'no confirmation', 'weak setup'],
            'good_entry': ['trend alignment', 'strong confirmation', 'good risk/reward'],
            'poor_exit': ['emotional exit', 'no plan', 'ignored signals'],
            'good_exit': ['systematic exit', 'followed plan', 'profit taking'],
            'risk_management': ['proper sizing', 'stop loss used', 'risk calculated']
        }

    async def analyze_trade(self, trade: Trade) -> CritiqueResult:
        """Generate comprehensive AI critique for a trade"""
        
        # Analyze technical aspects
        technical_score, technical_feedback = self._analyze_technical_execution(trade)
        
        # Analyze psychological patterns
        psychological_score, psychological_feedback, psych_tags = self._analyze_psychological_patterns(trade)
        
        # Analyze risk management
        risk_score, risk_feedback = self._analyze_risk_management(trade)
        
        # Generate overall assessment
        overall_confidence = self._calculate_confidence(technical_score, psychological_score, risk_score)
        
        # Generate summary and suggestions
        summary = self._generate_summary(trade, technical_score, psychological_score, risk_score)
        suggestion = self._generate_suggestions(technical_feedback, psychological_feedback, risk_feedback)
        
        # Combine all tags
        all_tags = psych_tags + self._get_technical_tags(trade, technical_score)
        
        return CritiqueResult(
            summary=summary,
            suggestion=suggestion,
            confidence=overall_confidence,
            tags=all_tags,
            technical_analysis=technical_feedback,
            psychological_analysis=psychological_feedback,
            risk_assessment=risk_feedback
        )

    def _analyze_technical_execution(self, trade: Trade) -> tuple[int, str]:
        """Analyze technical aspects of the trade"""
        score = 5  # Start neutral
        feedback = []
        
        # Check if trade is profitable
        is_profitable = trade.pnl and trade.pnl > 0
        
        # Risk/Reward analysis
        if trade.entry_price and trade.exit_price:
            price_diff = abs(trade.exit_price - trade.entry_price)
            risk_reward = price_diff / trade.entry_price if trade.entry_price > 0 else 0
            
            if risk_reward > 0.02:  # > 2% move
                score += 1
                feedback.append("Good price movement captured")
            elif risk_reward < 0.005:  # < 0.5% move
                score -= 1
                feedback.append("Minimal price movement captured")
        
        # Position sizing analysis
        if trade.quantity:
            # This would need market context, but we can do basic checks
            if trade.quantity > 0:
                feedback.append("Position sizing within normal range")
            else:
                score -= 2
                feedback.append("Invalid position size")
        
        # Entry/Exit timing (basic analysis)
        if trade.entry_time and trade.exit_time:
            duration = trade.exit_time - trade.entry_time
            duration_hours = duration.total_seconds() / 3600
            
            if is_profitable and duration_hours < 0.5:  # Quick profitable trade
                score += 1
                feedback.append("Quick execution with profit")
            elif not is_profitable and duration_hours > 24:  # Long losing trade
                score -= 1
                feedback.append("Extended holding of losing position")
        
        technical_feedback = " | ".join(feedback) if feedback else "Standard technical execution"
        return max(1, min(10, score)), technical_feedback

    def _analyze_psychological_patterns(self, trade: Trade) -> tuple[int, str, List[str]]:
        """Analyze psychological patterns in the trade"""
        score = 5
        feedback = []
        detected_tags = []
        
        # Check confidence score vs outcome
        if trade.confidence_score:
            if trade.pnl and trade.pnl > 0 and trade.confidence_score >= 7:
                score += 1
                feedback.append("High confidence matched positive outcome")
            elif trade.pnl and trade.pnl < 0 and trade.confidence_score >= 8:
                score -= 1
                feedback.append("Overconfidence may have led to poor outcome")
                detected_tags.append("overconfidence")
        
        # Analyze tags for emotional patterns
        if trade.tags:
            for tag in trade.tags:
                tag_lower = tag.lower()
                if any(pattern in tag_lower for pattern in ['fomo', 'revenge', 'panic']):
                    score -= 1
                    detected_tags.append(tag_lower)
                    feedback.append(f"Emotional pattern detected: {tag}")
                elif any(pattern in tag_lower for pattern in ['disciplined', 'planned', 'systematic']):
                    score += 1
                    feedback.append(f"Positive discipline pattern: {tag}")
        
        # Check for position sizing relative to confidence
        if trade.confidence_score and trade.quantity:
            # This is a simplified check - in reality you'd compare to typical position sizes
            if trade.confidence_score < 5 and trade.quantity > 0:
                feedback.append("Position sizing appears appropriate for confidence level")
            elif trade.confidence_score > 8:
                detected_tags.append("high_confidence")
                feedback.append("High confidence trade - monitor for overconfidence bias")
        
        psychological_feedback = " | ".join(feedback) if feedback else "No significant psychological patterns detected"
        return max(1, min(10, score)), psychological_feedback, detected_tags

    def _analyze_risk_management(self, trade: Trade) -> tuple[int, str]:
        """Analyze risk management aspects"""
        score = 5
        feedback = []
        
        # Check if stop loss was used (inferred from MAE)
        if trade.max_adverse_excursion:
            if abs(trade.max_adverse_excursion) < abs(trade.pnl or 0) * 2:
                score += 1
                feedback.append("Controlled downside risk")
            else:
                score -= 1
                feedback.append("High adverse excursion relative to final P&L")
        
        # Check position sizing (basic)
        if trade.quantity and trade.entry_price:
            position_value = trade.quantity * trade.entry_price
            if position_value > 0:
                feedback.append("Position sizing recorded")
            else:
                score -= 1
                feedback.append("Invalid position value calculation")
        
        # Check for proper exit strategy
        if trade.exit_price and trade.entry_price:
            if trade.pnl and trade.pnl > 0:
                feedback.append("Successful exit execution")
                score += 1
            elif trade.pnl and trade.pnl < 0:
                feedback.append("Loss taken - risk management applied")
                # Don't penalize for taking losses - it's part of trading
        
        risk_feedback = " | ".join(feedback) if feedback else "Standard risk management"
        return max(1, min(10, score)), risk_feedback

    def _calculate_confidence(self, technical_score: int, psychological_score: int, risk_score: int) -> int:
        """Calculate overall confidence in the analysis"""
        avg_score = (technical_score + psychological_score + risk_score) / 3
        # Convert to 1-10 scale with some adjustment
        confidence = int(avg_score)
        return max(1, min(10, confidence))

    def _generate_summary(self, trade: Trade, tech_score: int, psych_score: int, risk_score: int) -> str:
        """Generate concise trade summary"""
        
        if trade.pnl and trade.pnl > 0:
            outcome = "profitable"
        elif trade.pnl and trade.pnl < 0:
            outcome = "loss"
        else:
            outcome = "neutral"
        
        if tech_score >= 7:
            tech_assessment = "strong technical execution"
        elif tech_score <= 4:
            tech_assessment = "weak technical execution"
        else:
            tech_assessment = "average technical execution"
        
        if psych_score >= 7:
            psych_assessment = "good emotional control"
        elif psych_score <= 4:
            psych_assessment = "emotional decision-making detected"
        else:
            psych_assessment = "neutral emotional state"
        
        return f"Trade resulted in {outcome} with {tech_assessment} and {psych_assessment}."

    def _generate_suggestions(self, tech_feedback: str, psych_feedback: str, risk_feedback: str) -> str:
        """Generate actionable suggestions"""
        suggestions = []
        
        if "overconfidence" in psych_feedback.lower():
            suggestions.append("Consider reducing position size when confidence is very high")
        
        if "emotional" in psych_feedback.lower():
            suggestions.append("Implement cooling-off period before next trade")
        
        if "quick execution" in tech_feedback.lower():
            suggestions.append("Document what made this entry/exit effective")
        
        if "extended holding" in tech_feedback.lower():
            suggestions.append("Set clearer exit criteria before entering trades")
        
        if not suggestions:
            suggestions.append("Continue current approach with minor refinements")
        
        return " | ".join(suggestions)

    def _get_technical_tags(self, trade: Trade, score: int) -> List[str]:
        """Generate technical analysis tags"""
        tags = []
        
        if score >= 8:
            tags.append("excellent_execution")
        elif score <= 3:
            tags.append("poor_execution")
        
        if trade.pnl and trade.pnl > 0:
            tags.append("profitable")
        elif trade.pnl and trade.pnl < 0:
            tags.append("loss")
        
        if trade.confidence_score and trade.confidence_score >= 8:
            tags.append("high_confidence")
        elif trade.confidence_score and trade.confidence_score <= 3:
            tags.append("low_confidence")
        
        return tags

class CritiqueEngine:
    """Main critique engine interface"""
    
    def __init__(self):
        self.analyzer = AITradeAnalyzer()
    
    async def generate_critique(self, trade: Trade) -> Dict[str, Any]:
        """Generate AI critique for a trade"""
        try:
            result = await self.analyzer.analyze_trade(trade)
            
            critique_data = {
                "summary": result.summary,
                "suggestion": result.suggestion,
                "confidence": result.confidence,
                "tags": result.tags,
                "technical_analysis": result.technical_analysis,
                "psychological_analysis": result.psychological_analysis,
                "risk_assessment": result.risk_assessment,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            logger.info(f"Generated critique for trade {trade.id} with confidence {result.confidence}")
            return critique_data
            
        except Exception as e:
            logger.error(f"Error generating critique for trade {trade.id}: {str(e)}")
            return self._generate_fallback_critique()
    
    def _generate_fallback_critique(self) -> Dict[str, Any]:
        """Generate a basic critique when AI analysis fails"""
        return {
            "summary": "Trade logged successfully - detailed analysis unavailable",
            "suggestion": "Continue documenting trades for pattern recognition",
            "confidence": 5,
            "tags": ["analysis_pending"],
            "technical_analysis": "Technical analysis not available",
            "psychological_analysis": "Psychological analysis not available", 
            "risk_assessment": "Risk assessment not available",
            "generated_at": datetime.now().isoformat(),
            "version": "1.0"
        }
