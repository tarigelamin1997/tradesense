import streamlit as st
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime
from dataclasses import dataclass
from error_handler import ErrorHandler
from logging_manager import log_info, LogCategory
import re
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime
import json

class SupportSuggestion(NamedTuple):
    """Support suggestion structure."""
    issue_type: str
    confidence: float
    solution_steps: List[str]
    additional_resources: List[Dict[str, str]]
    escalation_needed: bool

class AutoSupportSystem:
    """Intelligent auto-support system with pattern matching."""

    def __init__(self):
        self.confidence_threshold = 0.6
        self.error_patterns = self._load_error_patterns()

    def _load_error_patterns(self) -> Dict:
        """Load error patterns and solutions."""
        return {
            "authentication_issues": {
                "patterns": [
                    r"(login|authentication|auth|credential|password|username).*(?:fail|error|invalid|wrong|incorrect)",
                    r"(token|session).*(?:expir|invalid|timeout)",
                    r"unable to.*(?:login|authenticate|connect)",
                    r"access.*(?:denied|forbidden|unauthorized)"
                ],
                "keywords": ["login", "password", "auth", "credential", "token", "session"],
                "solutions": [
                    "Verify your username and password are correct",
                    "Check if your account is locked or suspended", 
                    "Clear browser cookies and cache",
                    "Try using an incognito/private browser window",
                    "Reset your password if needed",
                    "Contact support if the issue persists"
                ],
                "resources": [
                    {"title": "Password Reset Guide", "url": "/help/password-reset"},
                    {"title": "Account Troubleshooting", "url": "/help/account-issues"}
                ]
            },

            "data_upload_issues": {
                "patterns": [
                    r"(upload|file|data|import).*(?:fail|error|problem|issue)",
                    r"(csv|excel|xlsx).*(?:invalid|corrupt|format|error)",
                    r"column.*(?:missing|not found|invalid)",
                    r"unable to.*(?:read|parse|process).*file"
                ],
                "keywords": ["upload", "file", "csv", "excel", "data", "import", "column"],
                "solutions": [
                    "Check that your file is in CSV or Excel format",
                    "Ensure required columns are present: symbol, entry_time, exit_time, pnl",
                    "Verify there are no special characters in column headers",
                    "Check that date formats are consistent (YYYY-MM-DD or MM/DD/YYYY)",
                    "Try uploading a smaller file first to test",
                    "Use our sample template for proper formatting"
                ],
                "resources": [
                    {"title": "File Format Guide", "url": "/help/file-formats"},
                    {"title": "Sample Data Template", "url": "/downloads/sample-template.csv"}
                ]
            },

            "connection_issues": {
                "patterns": [
                    r"(connection|connect|network).*(?:fail|error|timeout|refused|lost)",
                    r"unable to.*(?:connect|reach|access)",
                    r"(server|service).*(?:unavailable|down|offline)",
                    r"(timeout|timed out|no response)"
                ],
                "keywords": ["connection", "network", "server", "timeout", "offline"],
                "solutions": [
                    "Check your internet connection",
                    "Try refreshing the page",
                    "Clear browser cache and cookies",
                    "Disable VPN if you're using one",
                    "Try a different browser",
                    "Check if the service is down on our status page"
                ],
                "resources": [
                    {"title": "Connection Troubleshooting", "url": "/help/connection-issues"},
                    {"title": "Service Status", "url": "https://status.tradesense.app"}
                ]
            },

            "performance_issues": {
                "patterns": [
                    r"(slow|lag|freeze|hang|performance).*(?:issue|problem)",
                    r"(loading|render|display).*(?:slow|long|forever)",
                    r"browser.*(?:crash|freeze|unresponsive)",
                    r"charts?.*(?:not.*load|blank|empty)"
                ],
                "keywords": ["slow", "performance", "loading", "freeze", "crash", "lag"],
                "solutions": [
                    "Close unnecessary browser tabs and applications",
                    "Clear browser cache and cookies",
                    "Try reducing the date range of data being analyzed",
                    "Use Chrome or Firefox for best performance",
                    "Check if your system meets minimum requirements",
                    "Try accessing during off-peak hours"
                ],
                "resources": [
                    {"title": "Performance Optimization", "url": "/help/performance"},
                    {"title": "System Requirements", "url": "/help/requirements"}
                ]
            },

            "analytics_issues": {
                "patterns": [
                    r"(analytic|calculation|metric|chart).*(?:wrong|incorrect|error|missing)",
                    r"(report|export|pdf).*(?:fail|error|blank|empty)",
                    r"numbers.*(?:don't.*match|incorrect|wrong)",
                    r"(profit.*factor|win.*rate|sharpe|drawdown).*(?:incorrect|wrong)"
                ],
                "keywords": ["analytics", "calculation", "chart", "report", "export", "metrics"],
                "solutions": [
                    "Verify your trade data is complete and accurate",
                    "Check date range settings in filters",
                    "Ensure commission/fee data is included if applicable",
                    "Try refreshing the analysis",
                    "Clear filters and run analysis again",
                    "Compare with your broker's data for verification"
                ],
                "resources": [
                    {"title": "Analytics Guide", "url": "/help/analytics"},
                    {"title": "Metric Definitions", "url": "/help/metrics"}
                ]
            },

            "broker_specific": {
                "interactive_brokers": {
                    "patterns": [
                        r"(interactive.*brokers?|ibkr|ib|tws).*(?:error|fail|connection|issue)",
                        r"tws.*(?:not.*running|offline|disconnected)"
                    ],
                    "solutions": [
                        "Ensure TWS (Trader Workstation) is running",
                        "Check that API connections are enabled in TWS",
                        "Verify the correct port number (usually 7497 for paper, 7496 for live)",
                        "Make sure 'Enable ActiveX and Socket Clients' is checked",
                        "Try restarting TWS and reconnecting"
                    ]
                },
                "td_ameritrade": {
                    "patterns": [
                        r"(td.*ameritrade|tda|schwab).*(?:error|fail|connection|issue)",
                        r"oauth.*(?:error|fail|expired|invalid)"
                    ],
                    "solutions": [
                        "Check if your TD Ameritrade API access is still active",
                        "Verify your OAuth tokens haven't expired",
                        "Ensure your TD Ameritrade account has API permissions",
                        "Try re-authorizing your account connection"
                    ]
                }
            }
        }

    def analyze_issue(self, error_message: str = "", user_description: str = "") -> Optional[SupportSuggestion]:
        """Analyze an issue and provide auto-support suggestions."""
        combined_text = f"{error_message} {user_description}".lower()

        if not combined_text.strip():
            return None

        # Find the best matching issue type
        best_match = self._find_best_match(combined_text)

        if best_match and best_match[1] >= self.confidence_threshold:
            issue_type, confidence = best_match
            return self._generate_suggestion(issue_type, confidence, combined_text)

        return self._generate_generic_suggestion()

    def _find_best_match(self, text: str) -> Optional[Tuple[str, float]]:
        """Find the best matching issue type and confidence score."""
        scores = {}

        for issue_type, config in self.error_patterns.items():
            if issue_type == "broker_specific":
                # Handle broker-specific patterns
                for broker, broker_config in config.items():
                    broker_score = self._calculate_pattern_score(text, broker_config)
                    if broker_score > 0:
                        scores[f"{issue_type}_{broker}"] = broker_score
            else:
                score = self._calculate_pattern_score(text, config)
                if score > 0:
                    scores[issue_type] = score

        if not scores:
            return None

        # Return the highest scoring match
        best_issue = max(scores.items(), key=lambda x: x[1])
        return best_issue

    def _calculate_pattern_score(self, text: str, config: Dict) -> float:
        """Calculate confidence score for a pattern configuration."""
        pattern_score = 0.0
        keyword_score = 0.0

        # Check regex patterns
        patterns = config.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_score += 1.0

        # Check keywords
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text:
                keyword_score += 1.0

        # Normalize scores
        pattern_weight = 0.7
        keyword_weight = 0.3

        normalized_pattern_score = (pattern_score / len(patterns)) if patterns else 0
        normalized_keyword_score = (keyword_score / len(keywords)) if keywords else 0

        total_score = (pattern_weight * normalized_pattern_score) + (keyword_weight * normalized_keyword_score)

        return min(total_score, 1.0)  # Cap at 1.0

    def _generate_suggestion(self, issue_type: str, confidence: float, text: str) -> SupportSuggestion:
        """Generate a support suggestion for the identified issue type."""
        # Handle broker-specific issues
        if issue_type.startswith("broker_specific_"):
            broker = issue_type.split("_", 2)[2]
            config = self.error_patterns["broker_specific"][broker]

            return SupportSuggestion(
                issue_type=f"Broker Connection ({broker.replace('_', ' ').title()})",
                confidence=confidence,
                solution_steps=config["solutions"],
                additional_resources=[
                    {"title": f"{broker.replace('_', ' ').title()} Setup Guide", "url": f"/help/{broker}"}
                ],
                escalation_needed=confidence < 0.8
            )

        # Handle standard issue types
        config = self.error_patterns.get(issue_type, {})

        return SupportSuggestion(
            issue_type=issue_type.replace("_", " ").title(),
            confidence=confidence,
            solution_steps=config.get("solutions", []),
            additional_resources=config.get("resources", []),
            escalation_needed=confidence < 0.8
        )

    def _generate_generic_suggestion(self) -> SupportSuggestion:
        """Generate a generic suggestion when no specific pattern matches."""
        return SupportSuggestion(
            issue_type="General Issue",
            confidence=0.3,
            solution_steps=[
                "Try refreshing the page",
                "Clear your browser cache and cookies",
                "Check your internet connection",
                "Try using a different browser",
                "Contact our support team for personalized help"
            ],
            additional_resources=[
                {"title": "General Troubleshooting", "url": "/help/troubleshooting"},
                {"title": "Contact Support", "url": "/help/contact"}
            ],
            escalation_needed=True
        )

    def get_popular_solutions(self) -> List[Dict[str, str]]:
        """Get list of popular solutions for common issues."""
        return [
            {
                "title": "Clear Browser Cache",
                "description": "Solves many display and loading issues",
                "steps": "Press Ctrl+Shift+Delete and clear cache"
            },
            {
                "title": "Check File Format", 
                "description": "Ensure your data file has the correct format",
                "steps": "Use CSV or Excel with required columns"
            },
            {
                "title": "Refresh Connection",
                "description": "Reconnect to your broker account",
                "steps": "Go to Settings > Integrations > Reconnect"
            },
            {
                "title": "Update Browser",
                "description": "Use the latest version for best compatibility", 
                "steps": "Check for browser updates in settings"
            }
        ]

def render_auto_support_widget(error_message: str = "", user_description: str = ""):
    """Render auto-support widget for error resolution."""
    auto_support = AutoSupportSystem()
    
    if error_message or user_description:
        suggestion = auto_support.analyze_issue(error_message, user_description)
        
        if suggestion:
            st.success(f"🤖 **Auto-Support Suggestion** (Confidence: {suggestion.confidence:.0%})")
            
            with st.container():
                st.write(f"**{suggestion.issue_type}**")
                
                # Quick fix
                st.info(f"💡 **Possible Solutions:**")
                for step in suggestion.solution_steps:
                    st.write(f"- {step}")
                
                # Action buttons - removed old ones
                
                # Related documentation
                if suggestion.additional_resources:
                    st.write("**📚 Related Documentation:**")
                    for doc in suggestion.additional_resources:
                        st.write(f"• [{doc['title']}]({doc['url']})")
                
                # Auto-escalation notice
                if suggestion.escalation_needed:
                    st.warning("🔄 **Note:** This issue may require human assistance. We recommend contacting support if the above steps don't resolve the problem.")
        else:
            st.info("🤖 No specific auto-suggestion available. Please contact support for assistance.")

def quick_help_sidebar():
    """Render quick help in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🆘 Quick Help")
        
        help_options = [
            "Connection Issues",
            "Authentication Problems", 
            "Sync Errors",
            "General Questions"
        ]
        
        selected_help = st.selectbox("Get help with:", help_options)
        
        if st.button("🔍 Get Help"):
            auto_support = AutoSupportSystem()
            suggestion = auto_support.analyze_issue(user_description=selected_help)
            
            if suggestion:
                st.write(f"💡 {suggestion.solution_steps[0] if suggestion.solution_steps else 'Contact support for assistance'}")
            else:
                st.write("📞 Contact support for assistance")

if __name__ == "__main__":
    render_auto_support_widget()