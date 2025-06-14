
import streamlit as st
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime
from dataclasses import dataclass
from error_handler import ErrorHandler
from logging_manager import log_info, LogCategory

@dataclass
class SupportSuggestion:
    """Represents an auto-support suggestion."""
    title: str
    confidence: float
    quick_fix: str
    detailed_solution: List[str]
    related_docs: List[str]
    escalate_to_human: bool = False

class AutoSupport:
    """Intelligent auto-support system for common issues."""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.solution_templates = self._load_solution_templates()
        self.confidence_threshold = 0.7
    
    def _load_error_patterns(self) -> Dict:
        """Load error pattern recognition rules."""
        return {
            "authentication": {
                "patterns": [
                    r"(?i)(invalid|incorrect|wrong).*(credential|password|login)",
                    r"(?i)(auth|authentication).*(failed|error|denied)",
                    r"(?i)(token|session).*(expired|invalid)",
                    r"(?i)(unauthorized|access denied|forbidden)"
                ],
                "keywords": ["auth", "login", "credential", "token", "unauthorized", "forbidden"]
            },
            "connection": {
                "patterns": [
                    r"(?i)(connection|network).*(timeout|failed|refused|error)",
                    r"(?i)(server|host).*(unreachable|unavailable|down)",
                    r"(?i)(ssl|tls|certificate).*(error|invalid|expired)",
                    r"(?i)can.?t.*(connect|reach)"
                ],
                "keywords": ["connection", "network", "timeout", "server", "unreachable"]
            },
            "rate_limiting": {
                "patterns": [
                    r"(?i)(rate.?limit|too many requests|quota exceeded)",
                    r"(?i)(throttl|limit).*(exceeded|reached)",
                    r"(?i)429.*error"
                ],
                "keywords": ["rate limit", "quota", "throttle", "429", "too many"]
            },
            "data_sync": {
                "patterns": [
                    r"(?i)(sync|synchroniz).*(failed|error|incomplete)",
                    r"(?i)(missing|no).*(trade|data|record)",
                    r"(?i)(duplicate|repeated).*(trade|entry)",
                    r"(?i)(invalid|malformed).*(data|format)"
                ],
                "keywords": ["sync", "missing", "duplicate", "data", "trades"]
            },
            "broker_specific": {
                "interactive_brokers": {
                    "patterns": [
                        r"(?i)(ib|interactive.?brokers).*(error|failed)",
                        r"(?i)(tws|gateway).*(not.?running|unavailable)",
                        r"(?i)port.*(7496|7497).*(blocked|refused)"
                    ],
                    "keywords": ["ib", "tws", "gateway", "7496", "7497"]
                },
                "td_ameritrade": {
                    "patterns": [
                        r"(?i)(td|ameritrade).*(error|failed)",
                        r"(?i)(client.?id|refresh.?token).*(invalid|expired)"
                    ],
                    "keywords": ["td", "ameritrade", "client id", "refresh token"]
                }
            }
        }
    
    def _load_solution_templates(self) -> Dict:
        """Load solution templates for different issue types."""
        return {
            "authentication": {
                "title": "Authentication Issue Detected",
                "quick_fix": "Reconnect your account in the Integrations page",
                "detailed_solution": [
                    "1. Go to the Integrations page",
                    "2. Find the affected broker/account",
                    "3. Click 'Reconnect' or 'Edit Credentials'",
                    "4. Enter your current login information",
                    "5. Test the connection",
                    "6. If 2FA is enabled, ensure it's properly configured"
                ],
                "related_docs": ["authentication_guide", "broker_specific_auth"],
                "escalate_to_human": False
            },
            "connection": {
                "title": "Connection Problem Detected",
                "quick_fix": "Check your internet connection and broker status",
                "detailed_solution": [
                    "1. Verify your internet connection is stable",
                    "2. Check if your broker's servers are operational",
                    "3. Try connecting during off-peak hours",
                    "4. Disable VPN if you're using one",
                    "5. Check firewall settings",
                    "6. Contact your broker if the issue persists"
                ],
                "related_docs": ["connection_troubleshooting", "network_requirements"],
                "escalate_to_human": False
            },
            "rate_limiting": {
                "title": "Rate Limit Exceeded",
                "quick_fix": "Wait 15-30 minutes before trying again",
                "detailed_solution": [
                    "1. Wait for the rate limit window to reset (usually 15-60 minutes)",
                    "2. Reduce sync frequency in your settings",
                    "3. Avoid running multiple sync operations simultaneously",
                    "4. Contact your broker about increasing API limits",
                    "5. Consider upgrading to a higher-tier broker plan if available"
                ],
                "related_docs": ["rate_limiting_guide", "sync_optimization"],
                "escalate_to_human": False
            },
            "data_sync": {
                "title": "Data Synchronization Issue",
                "quick_fix": "Try syncing a smaller date range",
                "detailed_solution": [
                    "1. Check the selected date range - try a smaller period",
                    "2. Verify your account has permission to access trade history",
                    "3. Look for any account restrictions or limitations",
                    "4. Try manual sync instead of automatic",
                    "5. Check if there are any recent changes to your broker account"
                ],
                "related_docs": ["sync_troubleshooting", "data_permissions"],
                "escalate_to_human": True
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
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        return (best_type, best_score)
    
    def _calculate_pattern_score(self, text: str, config: Dict) -> float:
        """Calculate confidence score for a pattern match."""
        pattern_score = 0
        keyword_score = 0
        
        # Check regex patterns
        patterns = config.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text):
                pattern_score += 1
        
        # Check keywords
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword in text:
                keyword_score += 1
        
        # Calculate weighted score
        total_patterns = len(patterns) if patterns else 1
        total_keywords = len(keywords) if keywords else 1
        
        pattern_weight = 0.7
        keyword_weight = 0.3
        
        normalized_pattern_score = pattern_score / total_patterns
        normalized_keyword_score = keyword_score / total_keywords
        
        final_score = (normalized_pattern_score * pattern_weight + 
                      normalized_keyword_score * keyword_weight)
        
        return final_score
    
    def _generate_suggestion(self, issue_type: str, confidence: float, text: str) -> SupportSuggestion:
        """Generate a support suggestion based on issue type."""
        # Handle broker-specific issues
        base_type = issue_type.split("_")[0]
        template = self.solution_templates.get(base_type, self.solution_templates["authentication"])
        
        # Customize suggestion based on specific broker if applicable
        if "_" in issue_type:
            broker = issue_type.split("_")[1]
            template = self._customize_for_broker(template, broker)
        
        return SupportSuggestion(
            title=template["title"],
            confidence=confidence,
            quick_fix=template["quick_fix"],
            detailed_solution=template["detailed_solution"],
            related_docs=template["related_docs"],
            escalate_to_human=template.get("escalate_to_human", False)
        )
    
    def _customize_for_broker(self, template: Dict, broker: str) -> Dict:
        """Customize solution template for specific broker."""
        customized = template.copy()
        
        broker_customizations = {
            "interactive_brokers": {
                "quick_fix": "Ensure IB Gateway/TWS is running and check port configuration",
                "additional_steps": [
                    "• Verify IB Gateway or TWS is running",
                    "• Check port configuration (7497 for paper, 7496 for live)",
                    "• Ensure API access is enabled in your IB account"
                ]
            },
            "td_ameritrade": {
                "quick_fix": "Check your Client ID and refresh token",
                "additional_steps": [
                    "• Verify your Client ID from TD Developer portal",
                    "• Check if your refresh token has expired (90-day limit)",
                    "• Ensure account linking is properly configured"
                ]
            },
            "apex_trader": {
                "quick_fix": "Verify your API key and account ID",
                "additional_steps": [
                    "• Check if your API key is still valid",
                    "• Verify your account ID is correct",
                    "• Ensure your account status is active"
                ]
            }
        }
        
        if broker in broker_customizations:
            customization = broker_customizations[broker]
            customized["quick_fix"] = customization["quick_fix"]
            customized["detailed_solution"].extend(customization["additional_steps"])
        
        return customized
    
    def _generate_generic_suggestion(self) -> SupportSuggestion:
        """Generate a generic suggestion when no specific match is found."""
        return SupportSuggestion(
            title="General Support Guidance",
            confidence=0.5,
            quick_fix="Try basic troubleshooting steps or contact support",
            detailed_solution=[
                "1. Check your internet connection",
                "2. Verify your broker account is active",
                "3. Review recent changes to your account settings",
                "4. Try disconnecting and reconnecting the integration",
                "5. Contact support with specific error details"
            ],
            related_docs=["general_troubleshooting", "contact_support"],
            escalate_to_human=True
        )
    
    def render_auto_suggestion(self, suggestion: SupportSuggestion):
        """Render auto-support suggestion in Streamlit UI."""
        confidence_color = "green" if suggestion.confidence >= 0.8 else "orange" if suggestion.confidence >= 0.6 else "red"
        
        st.success(f"🤖 **Auto-Support Suggestion** (Confidence: {suggestion.confidence:.0%})")
        
        with st.container():
            st.write(f"**{suggestion.title}**")
            
            # Quick fix
            st.info(f"💡 **Quick Fix:** {suggestion.quick_fix}")
            
            # Detailed solution
            with st.expander("📋 Detailed Steps", expanded=True):
                for step in suggestion.detailed_solution:
                    st.write(step)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ This Helped", key="helpful"):
                    st.success("Great! Glad we could help.")
                    self._log_feedback("helpful", suggestion)
            
            with col2:
                if st.button("❌ Didn't Help", key="not_helpful"):
                    st.warning("Sorry this didn't help. We'll escalate to human support.")
                    self._log_feedback("not_helpful", suggestion)
                    self._escalate_to_human()
            
            with col3:
                if st.button("📞 Talk to Human", key="escalate"):
                    self._escalate_to_human()
            
            # Related documentation
            if suggestion.related_docs:
                st.write("**📚 Related Documentation:**")
                for doc in suggestion.related_docs:
                    st.write(f"• [{doc.replace('_', ' ').title()}](#{doc})")
            
            # Auto-escalation notice
            if suggestion.escalate_to_human:
                st.warning("🔄 **Note:** This issue may require human assistance. We recommend contacting support if the above steps don't resolve the problem.")
    
    def _log_feedback(self, feedback_type: str, suggestion: SupportSuggestion):
        """Log user feedback on auto-support suggestions."""
        feedback_data = {
            "feedback_type": feedback_type,
            "suggestion_title": suggestion.title,
            "confidence": suggestion.confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        log_info(
            f"Auto-support feedback: {feedback_type}",
            details=feedback_data,
            category=LogCategory.USER_ACTION
        )
    
    def _escalate_to_human(self):
        """Escalate issue to human support."""
        st.info("🔄 **Escalating to Human Support**")
        st.write("A support ticket has been created and our team will contact you within 24 hours.")
        
        # In a real implementation, this would create a support ticket
        ticket_id = f"AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.success(f"**Ticket ID:** {ticket_id}")

def render_auto_support_widget(error_message: str = "", user_description: str = ""):
    """Render auto-support widget for error resolution."""
    auto_support = AutoSupport()
    
    if error_message or user_description:
        suggestion = auto_support.analyze_issue(error_message, user_description)
        
        if suggestion:
            auto_support.render_auto_suggestion(suggestion)
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
            auto_support = AutoSupport()
            suggestion = auto_support.analyze_issue(user_description=selected_help)
            
            if suggestion:
                st.write(f"💡 {suggestion.quick_fix}")
            else:
                st.write("📞 Contact support for assistance")

if __name__ == "__main__":
    render_auto_support_widget()
