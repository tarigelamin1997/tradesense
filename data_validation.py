import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re
from datetime import datetime, timedelta
import streamlit as st
import html
import bleach


class InputSanitizer:
    """Input sanitization utilities for security."""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent XSS and injection attacks."""
        if not value:
            return ""

        # Remove null bytes and control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in ['\n', '\r', '\t'])

        # HTML escape
        value = html.escape(value)

        # Use bleach for additional sanitization
        allowed_tags = []  # No tags allowed for basic string input
        value = bleach.clean(value, tags=allowed_tags, strip=True)

        # Limit length to prevent buffer overflow
        max_length = 255
        if len(value) > max_length:
            value = value[:max_length]

        return value.strip()

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email input."""
        if not email:
            return ""

        # Basic email sanitization
        email = email.strip().lower()

        # Remove dangerous characters
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789@.-_+'
        email = ''.join(char for char in email if char in allowed_chars)

        return email

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not filename:
            return ""

        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            filename = filename[:255]

        return filename.strip()

class DataValidator:
    """Comprehensive data validation and correction system for trade data."""

    def __init__(self):
        self.validation_rules = {
            'symbol': self._validate_symbol,
            'entry_time': self._validate_datetime,
            'exit_time': self._validate_datetime,
            'entry_price': self._validate_price,
            'exit_price': self._validate_price,
            'qty': self._validate_quantity,
            'direction': self._validate_direction,
            'pnl': self._validate_pnl,
            'trade_type': self._validate_trade_type,
            'broker': self._validate_broker
        }

    def validate_and_clean_data(self, df: pd.DataFrame, interactive: bool = True) -> Tuple[pd.DataFrame, dict]:
        """Main validation and cleaning function."""
        if df.empty:
            return df, self._generate_report(df, [], ["Input DataFrame is empty"], 0)

        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        original_rows = len(df_copy)

        # Ensure required columns exist
        from data_import.base_importer import REQUIRED_COLUMNS
        missing_required = [col for col in REQUIRED_COLUMNS if col not in df_copy.columns]
        if missing_required:
            issues = [f"Missing required columns: {', '.join(missing_required)}"]
            return df_copy, self._generate_report(df_copy, [], issues, original_rows)

        corrections = []
        issues = []

        try:
            # Verify critical columns exist before processing
            critical_processing_cols = ['entry_time', 'exit_time', 'symbol']
            missing_critical = [col for col in critical_processing_cols if col not in df_copy.columns]
            if missing_critical:
                issues.append(f"Critical columns missing before validation: {', '.join(missing_critical)}")
                return df_copy, self._generate_report(df_copy, corrections, issues, original_rows)

            # Fix data types first - but preserve the DataFrame structure
            try:
                df_copy, type_corrections = self._fix_data_types(df_copy)
                corrections.extend(type_corrections)

                # Check if DataFrame became empty after type fixing
                if df_copy.empty:
                    issues.append("DataFrame became empty after type conversion")
                    return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

            except Exception as e:
                issues.append(f"Error fixing data types: {str(e)}")
                return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

            # Validate each column with safety checks
            for column in self.validation_rules.keys():
                if column in df_copy.columns:
                    try:
                        df_copy, column_issues = self._validate_column(df_copy, column, interactive)
                        issues.extend(column_issues)

                        # Safety check: ensure DataFrame is not empty
                        if df_copy.empty:
                            issues.append(f"DataFrame became empty after validating column {column}")
                            return df, self._generate_report(df, corrections, issues, original_rows)

                    except Exception as e:
                        issues.append(f"Error validating column {column}: {str(e)}")

            # Validate logical consistency with safety checks
            try:
                df_copy, logic_issues = self._validate_logical_consistency(df_copy, interactive)
                issues.extend(logic_issues)

                # Safety check after logical validation
                if df_copy.empty:
                    issues.append("DataFrame became empty after logical consistency validation")
                    return df, self._generate_report(df, corrections, issues, original_rows)

            except Exception as e:
                issues.append(f"Error in logical consistency validation: {str(e)}")

            # Remove completely invalid rows with safety check
            try:
                rows_before_removal = len(df_copy)
                df_copy = self._remove_invalid_rows(df_copy)
                rows_after_removal = len(df_copy)

                # If too many rows were removed, warn but don't return empty DataFrame
                if rows_after_removal == 0 and rows_before_removal > 0:
                    issues.append("All rows were marked as invalid and removed")
                    return df, self._generate_report(df, corrections, issues, original_rows)
                elif rows_after_removal < rows_before_removal * 0.1:  # More than 90% removed
                    issues.append(f"Warning: {rows_before_removal - rows_after_removal} of {rows_before_removal} rows removed ({((rows_before_removal - rows_after_removal)/rows_before_removal*100):.1f}%)")

            except Exception as e:
                issues.append(f"Error removing invalid rows: {str(e)}")

            # Final check to ensure required columns still exist
            final_missing = [col for col in REQUIRED_COLUMNS if col not in df_copy.columns]
            if final_missing:
                issues.append(f"Required columns lost during validation: {', '.join(final_missing)}")
                return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

            # Extra check for critical processing columns
            critical_missing = [col for col in critical_processing_cols if col not in df_copy.columns]
            if critical_missing:
                issues.append(f"Critical processing columns lost: {', '.join(critical_missing)}")
                return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

        except Exception as e:
            issues.append(f"Critical validation error: {str(e)}")
            return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

        # Final safety check before returning
        if df_copy.empty or len(df_copy.columns) == 0:
            issues.append("Final safety check failed: DataFrame is empty or has no columns")
            return df, self._generate_report(df, corrections, issues, original_rows)  # Return original

        return df_copy, self._generate_report(df_copy, corrections, issues, original_rows)

    def _fix_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Fix basic data type issues."""
        corrections = []

        # Fix numeric columns
        numeric_cols = ['entry_price', 'exit_price', 'qty', 'pnl']
        for col in numeric_cols:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if original_type != df[col].dtype:
                    corrections.append(f"Converted {col} to numeric type")

        # Fix datetime columns
        datetime_cols = ['entry_time', 'exit_time']
        for col in datetime_cols:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_datetime(df[col], errors='coerce')
                if original_type != df[col].dtype:
                    corrections.append(f"Converted {col} to datetime type")

        # Fix string columns
        string_cols = ['symbol', 'direction', 'trade_type', 'broker']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                corrections.append(f"Cleaned {col} string values")

        return df, corrections

    def _validate_column(self, df: pd.DataFrame, column: str, interactive: bool) -> Tuple[pd.DataFrame, List[str]]:
        """Validate individual column data."""
        issues = []

        if column not in df.columns:
            return df, issues

        validator_func = self.validation_rules[column]

        for idx, value in df[column].items():
            is_valid, corrected_value, issue_desc = validator_func(value, df.loc[idx] if idx in df.index else None)

            if not is_valid:
                issues.append(f"Row {idx}: {column} - {issue_desc}")

                if interactive and corrected_value is not None:
                    df.at[idx, column] = corrected_value
                elif not interactive and corrected_value is not None:
                    df.at[idx, column] = corrected_value

        return df, issues

    def _validate_symbol(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate symbol field."""
        if pd.isna(value) or value == '' or str(value).strip() == '':
            return False, None, "Empty symbol"

        symbol = str(value).strip().upper()

        # Remove invalid characters
        cleaned_symbol = ''.join(char for char in symbol if char.isalnum() or char in ['-', '.', '/'])

        if len(cleaned_symbol) < 1:
            return False, None, "Symbol too short after cleaning"

        if len(cleaned_symbol) > 20:
            return False, cleaned_symbol[:20], "Symbol too long, truncated"

        cleaned_symbol = self._sanitize_input(cleaned_symbol)

        return True, cleaned_symbol, ""

    def _validate_datetime(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate datetime fields."""
        if pd.isna(value):
            return False, None, "Missing datetime"

        try:
            dt = pd.to_datetime(value)

            # Check for reasonable date range
            min_date = datetime(2000, 1, 1)
            max_date = datetime.now() + timedelta(days=1)

            if dt < min_date:
                return False, min_date, f"Date too old ({dt}), set to minimum"

            if dt > max_date:
                return False, max_date, f"Future date ({dt}), set to current"

            return True, dt, ""

        except Exception:
            return False, None, "Invalid datetime format"

    def _validate_price(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate price fields."""
        if pd.isna(value):
            return False, None, "Missing price"

        try:
            price = float(value)

            if not np.isfinite(price):
                return False, None, "Infinite or NaN price"

            if price <= 0:
                return False, None, "Non-positive price"

            if price > 1000000:
                return False, 1000000, "Extremely high price, capped at $1M"

            return True, price, ""

        except Exception:
            return False, None, "Invalid price format"

    def _validate_quantity(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate quantity field."""
        if pd.isna(value):
            return False, 1, "Missing quantity, set to 1"

        try:
            qty = float(value)

            if not np.isfinite(qty):
                return False, 1, "Infinite quantity, set to 1"

            if qty <= 0:
                return False, 1, "Non-positive quantity, set to 1"

            if qty > 1000000:
                return False, 1000000, "Extremely high quantity, capped"

            return True, qty, ""

        except Exception:
            return False, 1, "Invalid quantity format, set to 1"

    def _validate_direction(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate direction field."""
        if pd.isna(value) or str(value).strip() == '':
            return False, 'long', "Missing direction, set to 'long'"

        direction = str(value).lower().strip()

        valid_directions = {
            'long': 'long',
            'short': 'short',
            'buy': 'long',
            'sell': 'short',
            'l': 'long',
            's': 'short',
            '1': 'long',
            '-1': 'short'
        }

        if direction in valid_directions:
            return True, valid_directions[direction], ""

        direction = self._sanitize_input(direction)
        return False, 'long', f"Invalid direction '{value}', set to 'long'"

    def _validate_pnl(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate P&L field."""
        if pd.isna(value):
            # Try to calculate from other fields if available
            if row is not None:
                calculated_pnl = self._calculate_pnl_from_row(row)
                if calculated_pnl is not None:
                    return True, calculated_pnl, "Calculated P&L from prices"
            return False, 0, "Missing P&L, set to 0"

        try:
            pnl = float(value)

            if not np.isfinite(pnl):
                return False, 0, "Infinite P&L, set to 0"

            # Very large P&L values might be errors
            if abs(pnl) > 1000000:
                return False, np.sign(pnl) * 1000000, "Extremely large P&L, capped"

            return True, pnl, ""

        except Exception:
            return False, 0, "Invalid P&L format, set to 0"

    def _validate_trade_type(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate trade type field."""
        if pd.isna(value) or str(value).strip() == '':
            return True, 'manual', "Set trade_type to 'manual'"

        trade_type = str(value).lower().strip()
        valid_types = ['manual', 'auto', 'algorithm', 'system', 'imported']

        if trade_type in valid_types:
            return True, trade_type, ""

        trade_type = self._sanitize_input(trade_type)
        return True, 'manual', f"Unknown trade_type '{value}', set to 'manual'"

    def _validate_broker(self, value: Any, row: pd.Series = None) -> Tuple[bool, Any, str]:
        """Validate broker field."""
        if pd.isna(value) or str(value).strip() == '':
            return True, 'unknown', "Set broker to 'unknown'"

        broker = str(value).strip()
        broker = self._sanitize_input(broker)
        return True, broker, ""

    def _calculate_pnl_from_row(self, row: pd.Series) -> float:
        """Calculate P&L from entry/exit prices if possible."""
        try:
            if all(col in row for col in ['entry_price', 'exit_price', 'qty', 'direction']):
                entry = float(row['entry_price'])
                exit_price = float(row['exit_price'])
                qty = float(row['qty'])
                direction = str(row['direction']).lower()

                if direction in ['long', 'buy']:
                    return (exit_price - entry) * qty
                elif direction in ['short', 'sell']:
                    return (entry - exit_price) * qty

        except Exception:
            pass

        return None

    def _validate_logical_consistency(self, df: pd.DataFrame, interactive: bool) -> Tuple[pd.DataFrame, List[str]]:
        """Validate logical consistency across columns."""
        issues = []

        for idx, row in df.iterrows():
            # Check if exit_time > entry_time
            if 'entry_time' in row and 'exit_time' in row:
                if pd.notna(row['entry_time']) and pd.notna(row['exit_time']):
                    if row['exit_time'] <= row['entry_time']:
                        issues.append(f"Row {idx}: Exit time is before or same as entry time")
                        # Fix by adding 1 minute to exit time
                        df.at[idx, 'exit_time'] = row['entry_time'] + timedelta(minutes=1)

            # Check P&L consistency with prices and direction
            if all(col in row for col in ['entry_price', 'exit_price', 'qty', 'direction', 'pnl']):
                if all(pd.notna(row[col]) for col in ['entry_price', 'exit_price', 'qty', 'direction', 'pnl']):
                    calculated_pnl = self._calculate_pnl_from_row(row)
                    if calculated_pnl is not None:
                        actual_pnl = float(row['pnl'])
                        if abs(calculated_pnl - actual_pnl) > 0.01:  # Allow small rounding differences
                            issues.append(f"Row {idx}: P&L doesn't match calculated value")
                            if interactive:
                                df.at[idx, 'pnl'] = calculated_pnl

        return df, issues

    def _remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that are completely invalid."""
        # Remove rows where critical fields are all missing
        critical_fields = ['symbol', 'entry_price', 'exit_price', 'entry_time', 'exit_time']

        # Only remove rows if they have missing data in critical fields
        # But ensure we don't remove ALL rows
        initial_rows = len(df)

        for field in critical_fields:
            if field in df.columns:
                rows_before = len(df)
                df = df[df[field].notna()]
                rows_after = len(df)

                # If this removal would empty the DataFrame, stop and return what we have
                if rows_after == 0 and initial_rows > 0:
                    # Restore the DataFrame to the previous state
                    df = pd.DataFrame(df_data) if 'df_data' in locals() else df
                    break

        return df

    def _calculate_quality_score(self, original_rows: int, final_rows: int, issues_count: int) -> float:
        """Calculate data quality score (0-100)."""
        if original_rows == 0:
            return 100.0

        retention_rate = final_rows / original_rows
        issue_penalty = min(issues_count / original_rows, 0.5)  # Cap penalty at 50%

        quality_score = (retention_rate * 100) - (issue_penalty * 100)
        return max(0.0, min(100.0, quality_score))

    def _generate_report(self, df: pd.DataFrame, corrections: List[str], issues: List[str], original_rows: int = None) -> Dict:
        """Generate a data quality report."""
        final_rows = len(df)
        issues_count = len(issues)
        if original_rows is None:
            original_rows = final_rows  # If original_rows is not provided, assume no rows were removed initially

        data_quality_score = self._calculate_quality_score(original_rows, final_rows, issues_count)

        report = {
            'original_rows': original_rows,
            'issues_found': issues,
            'corrections_made': corrections,
            'final_rows': final_rows,
            'data_quality_score': data_quality_score
        }
        return report

    def _sanitize_input(self, value: str) -> str:
        """Sanitize untrusted input to prevent XSS and other injection attacks."""

        # Escape HTML entities
        value = html.escape(value)

        # Use bleach to strip unwanted tags and attributes
        allowed_tags = ['b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'p', 'br', 'span']
        allowed_attributes = {'a': ['href', 'title'], 'span': ['style']}
        value = bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        return value

    def validate_and_clean(self, df: pd.DataFrame, interactive: bool = True) -> Tuple[pd.DataFrame, dict]:
        """Compatibility alias for validate_and_clean_data method."""
        return self.validate_and_clean_data(df, interactive)

    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            'original_rows': 0,
            'issues_found': [],
            'corrections_made': [],
            'final_rows': 0,
            'data_quality_score': 0.0
        }


def create_data_correction_interface(df: pd.DataFrame, validator: DataValidator) -> pd.DataFrame:
    """Create interactive interface for data correction."""

    st.subheader("🔧 Data Validation & Correction")

    # Run validation
    with st.spinner("Analyzing data quality..."):
        cleaned_df, report = validator.validate_and_clean_data(df, interactive=False)

    # Display quality report
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Data Quality Score", f"{report['data_quality_score']:.1f}%")

    with col2:
        retention_rate = (report['final_rows'] / report['original_rows'] * 100) if report['original_rows'] > 0 else 100
        st.metric("Data Retention", f"{retention_rate:.1f}%")

    with col3:
        st.metric("Issues Found", len(report['issues_found']))

    # Show issues if any
    if report['issues_found']:
        with st.expander(f"⚠️ Data Issues Found ({len(report['issues_found'])})", expanded=True):
            for issue in report['issues_found'][:10]:  # Show first 10 issues
                st.warning(issue)

            if len(report['issues_found']) > 10:
                st.info(f"... and {len(report['issues_found']) - 10} more issues")

    # Show corrections made
    if report['corrections_made']:
        with st.expander(f"✅ Corrections Applied ({len(report['corrections_made'])})"):
            for correction in report['corrections_made']:
                st.success(correction)

    # Offer correction options
    st.write("**Correction Options:**")

    correction_mode = st.radio(
        "How would you like to handle data issues?",
        [
            "🔧 Auto-fix (Recommended) - Automatically correct common issues",
            "📋 Manual review - Show issues for manual correction",
            "🗑️ Remove invalid - Remove rows with issues",
            "✋ Use as-is - Proceed with original data"
        ]
    )

    if correction_mode.startswith("🔧"):
        st.success("✅ Auto-fix applied - Data has been automatically corrected where possible")
        return cleaned_df

    elif correction_mode.startswith("📋"):
        return create_manual_correction_interface(df, report)

    elif correction_mode.startswith("🗑️"):
        # Remove rows with any issues
        issue_rows = set()
        for issue in report['issues_found']:
            try:
                row_num = int(issue.split(':')[0].replace('Row ', ''))
                issue_rows.add(row_num)
            except:
                pass

        clean_df = df.drop(index=list(issue_rows))
        st.info(f"Removed {len(issue_rows)} rows with issues. {len(clean_df)} rows remain.")
        return clean_df

    else:  # Use as-is
        st.warning("⚠️ Proceeding with original data - Some analytics may show errors")
        return df


def create_manual_correction_interface(df: pd.DataFrame, report: Dict) -> pd.DataFrame:
    """Create interface for manual data correction."""

    st.write("**Manual Data Correction**")

    # Group issues by row
    row_issues = {}
    for issue in report['issues_found']:
        try:
            row_num = int(issue.split(':')[0].replace('Row ', ''))
            if row_num not in row_issues:
                row_issues[row_num] = []
            row_issues[row_num].append(issue)
        except:
            continue

    if not row_issues:
        st.success("No issues found that require manual correction!")
        return df

    # Let user select which rows to fix
    st.write(f"Found issues in {len(row_issues)} rows:")

    rows_to_fix = st.multiselect(
        "Select rows to review and fix:",
        options=list(row_issues.keys()),
        default=list(row_issues.keys())[:5],  # Default to first 5
        format_func=lambda x: f"Row {x} ({len(row_issues[x])} issues)"
    )

    corrected_df = df.copy()

    for row_idx in rows_to_fix:
        if row_idx in df.index:
            st.write(f"**Row {row_idx} Issues:**")
            for issue in row_issues[row_idx]:
                st.error(issue)

            # Show current row data
            row_data = df.loc[row_idx]

            with st.expander(f"Edit Row {row_idx}", expanded=True):
                col1, col2 = st.columns(2)

                # Create edit fields for each column
                updated_values = {}

                for i, (col, value) in enumerate(row_data.items()):
                    with col1 if i % 2 == 0 else col2:
                        if col in ['entry_price', 'exit_price', 'qty', 'pnl']:
                            updated_values[col] = st.number_input(
                                f"{col}:",
                                value=float(value) if pd.notna(value) and np.isfinite(float(value)) else 0.0,
                                key=f"edit_{row_idx}_{col}"
                            )
                        elif col in ['entry_time', 'exit_time']:
                            updated_values[col] = st.date_input(
                                f"{col}:",
                                value=pd.to_datetime(value).date() if pd.notna(value) else datetime.now().date(),
                                key=f"edit_{row_idx}_{col}"
                            )
                        elif col == 'direction':
                            updated_values[col] = st.selectbox(
                                f"{col}:",
                                options=['long', 'short'],
                                index=0 if str(value).lower() in ['long', 'buy'] else 1,
                                key=f"edit_{row_idx}_{col}"
                            )
                        else:
                            # Sanitize text input
                            text_value = str(value) if pd.notna(value) else ""
                            sanitized_value = validator._sanitize_input(text_value)
                            updated_values[col] = st.text_input(
                                f"{col}:",
                                value=sanitized_value,
                                key=f"edit_{row_idx}_{col}"
                            )

                if st.button(f"Apply Changes to Row {row_idx}", key=f"apply_{row_idx}"):
                    for col, new_value in updated_values.items():
                        corrected_df.at[row_idx, col] = new_value
                    st.success(f"✅ Updated row {row_idx}")
                    st.rerun()

    return corrected_df