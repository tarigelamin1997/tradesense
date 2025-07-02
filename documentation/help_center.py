
import streamlit as st
from typing import Dict, List, Optional
import json
from datetime import datetime
from pathlib import Path

class HelpCenter:
    """Comprehensive help center with docs, FAQs, and auto-support."""
    
    def __init__(self):
        self.docs_path = Path("documentation/content")
        self.faqs_path = Path("documentation/faqs")
        self.search_index = {}
        self._load_content()
    
    def _load_content(self):
        """Load all documentation content and build search index."""
        # Create directories if they don't exist
        self.docs_path.mkdir(parents=True, exist_ok=True)
        self.faqs_path.mkdir(parents=True, exist_ok=True)
        
        # Load content into search index
        self._build_search_index()
    
    def _build_search_index(self):
        """Build searchable index of all help content."""
        self.search_index = {
            "brokers": {
                "interactive_brokers": {
                    "keywords": ["ib", "interactive brokers", "tws", "gateway", "authentication"],
                    "content_type": "broker_guide"
                },
                "td_ameritrade": {
                    "keywords": ["td", "ameritrade", "oauth", "tokens", "schwab"],
                    "content_type": "broker_guide"
                },
                "apex_trader": {
                    "keywords": ["apex", "prop firm", "funding", "challenge", "profit targets"],
                    "content_type": "prop_firm_guide"
                }
            },
            "errors": {
                "authentication": {
                    "keywords": ["login", "credential", "auth", "token", "expired"],
                    "content_type": "error_guide"
                },
                "connection": {
                    "keywords": ["connection", "network", "timeout", "server", "unreachable"],
                    "content_type": "error_guide"
                },
                "sync": {
                    "keywords": ["sync", "data", "trades", "missing", "incomplete"],
                    "content_type": "error_guide"
                }
            },
            "business": {
                "pricing": {
                    "keywords": ["price", "cost", "subscription", "billing", "payment"],
                    "content_type": "business_guide"
                },
                "features": {
                    "keywords": ["features", "analytics", "reports", "dashboard"],
                    "content_type": "business_guide"
                }
            }
        }
    
    def search_help(self, query: str) -> List[Dict]:
        """Search help content based on user query."""
        query_lower = query.lower()
        results = []
        
        for category, items in self.search_index.items():
            for item_key, item_data in items.items():
                # Check if any keywords match the query
                for keyword in item_data["keywords"]:
                    if keyword in query_lower:
                        results.append({
                            "category": category,
                            "item": item_key,
                            "content_type": item_data["content_type"],
                            "relevance": self._calculate_relevance(query_lower, item_data["keywords"])
                        })
                        break
        
        # Sort by relevance
        return sorted(results, key=lambda x: x["relevance"], reverse=True)
    
    def _calculate_relevance(self, query: str, keywords: List[str]) -> float:
        """Calculate relevance score for search results."""
        score = 0
        for keyword in keywords:
            if keyword in query:
                # Exact match gets higher score
                if keyword == query.strip():
                    score += 10
                else:
                    score += len(keyword)  # Longer matches get higher scores
        return score
    
    def get_auto_suggestion(self, error_message: str) -> Optional[Dict]:
        """Get automatic suggestion based on error message."""
        error_lower = error_message.lower()
        
        # Authentication errors
        if any(keyword in error_lower for keyword in ['auth', 'credential', 'login', 'token', 'unauthorized']):
            return {
                "type": "authentication_error",
                "title": "Authentication Issue Detected",
                "quick_fix": "Try reconnecting your account in the Integrations page",
                "detailed_guide": "authentication_troubleshooting"
            }
        
        # Connection errors
        elif any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return {
                "type": "connection_error",
                "title": "Connection Problem Detected",
                "quick_fix": "Check your internet connection and try again",
                "detailed_guide": "connection_troubleshooting"
            }
        
        # Rate limiting
        elif any(keyword in error_lower for keyword in ['rate limit', 'too many requests', 'quota']):
            return {
                "type": "rate_limit_error",
                "title": "Rate Limit Exceeded",
                "quick_fix": "Wait a few minutes before trying again",
                "detailed_guide": "rate_limiting_guide"
            }
        
        return None
    
    def render_help_center(self):
        """Render the main help center interface."""
        st.title("🆘 TradeSense Help Center")
        st.markdown("---")
        
        # Search bar
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Search for help",
                placeholder="Enter your question or describe the issue..."
            )
        
        with col2:
            if st.button("🤖 AI Assistant", help="Get AI-powered help"):
                self._render_ai_assistant()
        
        # Quick search results
        if search_query:
            results = self.search_help(search_query)
            if results:
                st.subheader("📋 Search Results")
                for result in results[:5]:  # Show top 5 results
                    with st.expander(f"📄 {result['item'].replace('_', ' ').title()} ({result['category']})"):
                        self._render_help_content(result['item'], result['content_type'])
        
        # Main navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔗 Broker Guides", 
            "❌ Error Solutions", 
            "💼 Business Info", 
            "❓ FAQs", 
            "📞 Contact Support"
        ])
        
        with tab1:
            self._render_broker_guides()
        
        with tab2:
            self._render_error_solutions()
        
        with tab3:
            self._render_business_info()
        
        with tab4:
            self._render_faqs()
        
        with tab5:
            self._render_contact_support()
    
    def _render_broker_guides(self):
        """Render broker-specific guides."""
        st.subheader("🏦 Broker Integration Guides")
        
        broker_guides = {
            "Interactive Brokers": {
                "icon": "🏛️",
                "difficulty": "Advanced",
                "setup_time": "10-15 minutes",
                "guide_key": "interactive_brokers"
            },
            "TD Ameritrade": {
                "icon": "🏢",
                "difficulty": "Intermediate", 
                "setup_time": "5-10 minutes",
                "guide_key": "td_ameritrade"
            },
            "Apex Trader Funding": {
                "icon": "🚀",
                "difficulty": "Easy",
                "setup_time": "3-5 minutes",
                "guide_key": "apex_trader"
            }
        }
        
        for broker_name, info in broker_guides.items():
            with st.expander(f"{info['icon']} {broker_name} - {info['difficulty']} Setup"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Difficulty", info['difficulty'])
                with col2:
                    st.metric("Setup Time", info['setup_time'])
                with col3:
                    if st.button(f"📖 Full Guide", key=f"guide_{info['guide_key']}"):
                        self._show_detailed_broker_guide(info['guide_key'])
                
                # Quick setup steps
                self._render_quick_setup_steps(info['guide_key'])
    
    def _render_quick_setup_steps(self, broker_key: str):
        """Render quick setup steps for each broker."""
        guides = {
            "interactive_brokers": {
                "steps": [
                    "1. Install IB Gateway or TWS on your computer",
                    "2. Enable API access in your IB account settings", 
                    "3. Configure socket port (7497 for paper, 7496 for live)",
                    "4. Add your IB credentials in TradeSense Integrations",
                    "5. Test connection and start syncing"
                ],
                "requirements": [
                    "Active Interactive Brokers account",
                    "IB Gateway or TWS installed locally",
                    "API access enabled"
                ],
                "common_issues": [
                    "Port conflicts - check firewall settings",
                    "Authentication timeout - verify credentials",
                    "Connection refused - ensure IB Gateway is running"
                ]
            },
            "td_ameritrade": {
                "steps": [
                    "1. Log into your TD Ameritrade account online",
                    "2. Navigate to API settings and create a new app",
                    "3. Copy your Client ID and generate refresh token",
                    "4. Add credentials to TradeSense Integrations", 
                    "5. Authorize account access and test connection"
                ],
                "requirements": [
                    "TD Ameritrade account with API access",
                    "Client ID from TD Developer portal",
                    "Valid refresh token"
                ],
                "common_issues": [
                    "Token expired - regenerate refresh token",
                    "Invalid client ID - check developer portal",
                    "Insufficient permissions - verify account settings"
                ]
            },
            "apex_trader": {
                "steps": [
                    "1. Log into your Apex Trader account portal",
                    "2. Navigate to API settings or integrations",
                    "3. Generate API key and copy account ID",
                    "4. Add credentials to TradeSense",
                    "5. Start automatic trade sync"
                ],
                "requirements": [
                    "Active Apex Trader account",
                    "API access enabled",
                    "Valid account ID"
                ],
                "common_issues": [
                    "API key invalid - regenerate from portal",
                    "Account not found - verify account ID",
                    "Sync errors - check account status"
                ]
            }
        }
        
        guide = guides.get(broker_key, {})
        
        if guide:
            st.write("**Quick Setup:**")
            for step in guide.get("steps", []):
                st.write(f"✅ {step}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Requirements:**")
                for req in guide.get("requirements", []):
                    st.write(f"• {req}")
            
            with col2:
                st.write("**Common Issues:**")
                for issue in guide.get("common_issues", []):
                    st.write(f"⚠️ {issue}")
    
    def _render_error_solutions(self):
        """Render error troubleshooting guides."""
        st.subheader("🔧 Error Troubleshooting")
        
        error_categories = {
            "Authentication Errors": {
                "icon": "🔐",
                "errors": [
                    "Invalid credentials",
                    "Token expired", 
                    "Unauthorized access",
                    "2FA required"
                ]
            },
            "Connection Issues": {
                "icon": "🌐",
                "errors": [
                    "Connection timeout",
                    "Server unreachable",
                    "Network error",
                    "Firewall blocking"
                ]
            },
            "Data Sync Problems": {
                "icon": "🔄",
                "errors": [
                    "Missing trades",
                    "Duplicate data",
                    "Sync failed",
                    "Invalid date range"
                ]
            },
            "Performance Issues": {
                "icon": "⚡",
                "errors": [
                    "Slow loading",
                    "Rate limit exceeded",
                    "Memory errors",
                    "Timeout errors"
                ]
            }
        }
        
        for category, info in error_categories.items():
            with st.expander(f"{info['icon']} {category}"):
                st.write("**Common errors in this category:**")
                
                for error in info['errors']:
                    if st.button(f"🔍 {error}", key=f"error_{error.replace(' ', '_')}"):
                        self._show_error_solution(error)
    
    def _show_error_solution(self, error_type: str):
        """Show detailed solution for specific error."""
        solutions = {
            "Invalid credentials": {
                "description": "Your login information is incorrect or outdated",
                "immediate_steps": [
                    "1. Verify credentials on broker's website",
                    "2. Check for recent password changes",
                    "3. Re-enter credentials in TradeSense"
                ],
                "prevention": "Enable credential auto-refresh where supported"
            },
            "Token expired": {
                "description": "Your authentication token has expired and needs renewal",
                "immediate_steps": [
                    "1. Go to Integrations page",
                    "2. Click 'Reconnect' for the affected account",
                    "3. Complete re-authentication process"
                ],
                "prevention": "Monitor token expiry dates and set up alerts"
            },
            "Connection timeout": {
                "description": "Unable to establish connection within time limit",
                "immediate_steps": [
                    "1. Check internet connection",
                    "2. Verify broker server status",
                    "3. Try again during off-peak hours"
                ],
                "prevention": "Use reliable internet connection and avoid peak trading hours"
            }
        }
        
        solution = solutions.get(error_type, {})
        
        if solution:
            st.success(f"💡 Solution for: {error_type}")
            st.write(f"**What this means:** {solution.get('description', 'Error description not available')}")
            
            st.write("**Immediate steps:**")
            for step in solution.get('immediate_steps', []):
                st.write(step)
            
            if solution.get('prevention'):
                st.info(f"**Prevention tip:** {solution['prevention']}")
    
    def _render_business_info(self):
        """Render business information and pricing."""
        st.subheader("💼 Business Information")
        
        business_sections = {
            "Pricing & Plans": {
                "icon": "💰",
                "content": self._render_pricing_info
            },
            "Features & Capabilities": {
                "icon": "⚡", 
                "content": self._render_features_info
            },
            "Data Security": {
                "icon": "🔒",
                "content": self._render_security_info
            },
            "Partner Program": {
                "icon": "🤝",
                "content": self._render_partner_info
            }
        }
        
        for section_name, section_info in business_sections.items():
            with st.expander(f"{section_info['icon']} {section_name}"):
                section_info['content']()
    
    def _render_pricing_info(self):
        """Render pricing information."""
        st.write("**TradeSense Pricing Plans:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**📊 Basic Plan - FREE**")
            st.write("• Up to 1,000 trades")
            st.write("• Basic analytics")
            st.write("• 1 broker connection")
            st.write("• Email support")
        
        with col2:
            st.write("**🚀 Pro Plan - $29/month**")
            st.write("• Unlimited trades")
            st.write("• Advanced analytics")
            st.write("• Multiple broker connections")
            st.write("• Real-time sync")
            st.write("• Priority support")
        
        with col3:
            st.write("**🏢 Enterprise - Custom**")
            st.write("• Custom integrations")
            st.write("• White-label options")
            st.write("• Dedicated support")
            st.write("• SLA guarantees")
    
    def _render_features_info(self):
        """Render features information."""
        features = {
            "Analytics & Reporting": [
                "Win rate and profit factor analysis",
                "Risk metrics and drawdown tracking", 
                "Performance over time charts",
                "Symbol and strategy breakdown"
            ],
            "Data Integration": [
                "30+ broker and prop firm connectors",
                "Real-time and historical data sync",
                "Automatic trade categorization",
                "Data validation and cleaning"
            ],
            "Risk Management": [
                "Position sizing recommendations",
                "Risk assessment tools",
                "Alert systems for drawdowns",
                "Portfolio diversification analysis"
            ]
        }
        
        for category, feature_list in features.items():
            st.write(f"**{category}:**")
            for feature in feature_list:
                st.write(f"✅ {feature}")
            st.write("")
    
    def _render_security_info(self):
        """Render security information."""
        st.write("**Data Security & Privacy:**")
        
        security_features = [
            "🔐 End-to-end encryption for all data transmission",
            "🏦 Bank-level security protocols and compliance",
            "🔑 Secure credential storage with industry standards",
            "🚫 No trading permissions - read-only access only",
            "📊 Local data processing - minimal cloud storage",
            "🔒 Regular security audits and penetration testing"
        ]
        
        for feature in security_features:
            st.write(feature)
        
        st.info("💡 **Note:** TradeSense never stores your trading passwords or has the ability to place trades. We only access historical trade data for analysis.")
    
    def _render_partner_info(self):
        """Render partner program information."""
        st.write("**Partner Program Benefits:**")
        
        partner_benefits = [
            "💰 Revenue sharing up to 30%",
            "🎨 White-label branding options", 
            "🔧 Custom integration development",
            "📈 Dedicated account management",
            "📊 Real-time partner analytics dashboard",
            "🎯 Marketing support and co-branding"
        ]
        
        for benefit in partner_benefits:
            st.write(benefit)
        
        if st.button("📞 Contact Partner Team"):
            st.success("Partner inquiry submitted! We'll contact you within 24 hours.")
    
    def _render_faqs(self):
        """Render frequently asked questions."""
        st.subheader("❓ Frequently Asked Questions")
        
        faqs = {
            "General": [
                {
                    "question": "How does TradeSense connect to my broker?",
                    "answer": "TradeSense uses read-only API connections to securely access your trading history. We never store passwords or have trading permissions."
                },
                {
                    "question": "Is my data secure?", 
                    "answer": "Yes! We use bank-level encryption and security protocols. All data is encrypted in transit and at rest, and we follow industry best practices."
                },
                {
                    "question": "Can TradeSense place trades on my behalf?",
                    "answer": "No, TradeSense only has read-only access to your trading history. We cannot place trades, modify positions, or access your funds."
                }
            ],
            "Technical": [
                {
                    "question": "Why isn't my broker showing up in the list?",
                    "answer": "We're continuously adding new broker integrations. Contact support to request your broker, and we'll prioritize it based on demand."
                },
                {
                    "question": "How often does data sync?",
                    "answer": "Data syncs every 15 minutes by default for Pro users, and daily for free users. You can also trigger manual syncs anytime."
                },
                {
                    "question": "What if I'm getting sync errors?",
                    "answer": "Check your credentials first, then verify your broker's API status. If issues persist, our error troubleshooting guide can help."
                }
            ],
            "Billing": [
                {
                    "question": "Can I cancel my subscription anytime?",
                    "answer": "Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your current billing period."
                },
                {
                    "question": "Do you offer refunds?",
                    "answer": "We offer a 30-day money-back guarantee for new subscribers. Contact support for refund requests."
                },
                {
                    "question": "Is there a free trial?",
                    "answer": "Yes! Our Basic plan is permanently free with limited features. Pro plan offers a 14-day free trial."
                }
            ]
        }
        
        for category, questions in faqs.items():
            st.write(f"**{category} Questions:**")
            
            for faq in questions:
                with st.expander(f"❓ {faq['question']}"):
                    st.write(faq['answer'])
    
    def _render_contact_support(self):
        """Render contact support options."""
        st.subheader("📞 Contact Support")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📧 Email Support**")
            st.write("• General questions: support@tradesense.com")
            st.write("• Technical issues: tech@tradesense.com") 
            st.write("• Business inquiries: business@tradesense.com")
            st.write("• Response time: 24-48 hours")
        
        with col2:
            st.write("**💬 Live Chat**")
            st.write("• Available Mon-Fri 9AM-6PM EST")
            st.write("• Priority support for Pro users")
            st.write("• Average response: < 2 hours")
        
        st.markdown("---")
        
        # Support ticket form
        st.subheader("🎫 Submit Support Ticket")
        
        with st.form("support_ticket"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Your Name")
                email = st.text_input("Email Address")
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
            
            with col2:
                category = st.selectbox("Category", [
                    "Technical Issue",
                    "Billing Question", 
                    "Feature Request",
                    "General Question",
                    "Bug Report"
                ])
                broker = st.selectbox("Related Broker (if applicable)", [
                    "Not applicable",
                    "Interactive Brokers",
                    "TD Ameritrade", 
                    "Apex Trader",
                    "Other"
                ])
            
            subject = st.text_input("Subject")
            description = st.text_area("Describe your issue or question", height=150)
            
            # File upload for screenshots
            uploaded_files = st.file_uploader(
                "Upload screenshots or logs (optional)",
                accept_multiple_files=True,
                type=['png', 'jpg', 'jpeg', 'pdf', 'txt', 'log']
            )
            
            if st.form_submit_button("📤 Submit Ticket"):
                if name and email and subject and description:
                    # Save ticket (in real implementation, this would go to a ticketing system)
                    ticket_id = f"TS{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    st.success(f"✅ Support ticket submitted successfully!")
                    st.info(f"**Ticket ID:** {ticket_id}")
                    st.write("You'll receive a confirmation email shortly.")
                    
                    # Log the support ticket
                    self._log_support_ticket({
                        "ticket_id": ticket_id,
                        "name": name,
                        "email": email,
                        "category": category,
                        "priority": priority,
                        "subject": subject,
                        "description": description,
                        "broker": broker,
                        "files": len(uploaded_files) if uploaded_files else 0,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    st.error("Please fill in all required fields")
    
    def _log_support_ticket(self, ticket_data: Dict):
        """Log support ticket for tracking."""
        try:
            # In a real implementation, this would save to a database
            # For now, we'll just log it
            import json
            ticket_json = json.dumps(ticket_data, indent=2)
            print(f"Support ticket logged: {ticket_json}")
        except Exception as e:
            print(f"Error logging support ticket: {e}")
    
    def _render_ai_assistant(self):
        """Render AI assistant interface."""
        st.subheader("🤖 AI Help Assistant")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat interface
        user_input = st.text_input("Ask me anything about TradeSense...")
        
        if st.button("Send") and user_input:
            # Add user message
            st.session_state.chat_history.append({
                "type": "user",
                "message": user_input,
                "timestamp": datetime.now()
            })
            
            # Generate AI response (simplified)
            ai_response = self._generate_ai_response(user_input)
            
            st.session_state.chat_history.append({
                "type": "assistant", 
                "message": ai_response,
                "timestamp": datetime.now()
            })
        
        # Display chat history
        for chat in st.session_state.chat_history[-5:]:  # Show last 5 messages
            if chat["type"] == "user":
                st.write(f"**You:** {chat['message']}")
            else:
                st.write(f"**Assistant:** {chat['message']}")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    def _generate_ai_response(self, user_input: str) -> str:
        """Generate AI response based on user input."""
        input_lower = user_input.lower()
        
        # Simple rule-based responses (in production, use actual AI)
        if any(word in input_lower for word in ['price', 'cost', 'billing', 'subscription']):
            return "Our pricing starts with a free Basic plan, then $29/month for Pro. Would you like me to show you our full pricing details?"
        
        elif any(word in input_lower for word in ['broker', 'connect', 'integration']):
            return "I can help you connect your broker! We support Interactive Brokers, TD Ameritrade, Apex Trader, and more. Which broker are you trying to connect?"
        
        elif any(word in input_lower for word in ['error', 'problem', 'issue', 'broken']):
            return "I'm sorry you're experiencing issues! Can you describe the specific error message or problem you're seeing? I can provide targeted troubleshooting steps."
        
        elif any(word in input_lower for word in ['secure', 'security', 'safe', 'privacy']):
            return "Security is our top priority! We use bank-level encryption, read-only access, and never store your trading passwords. Your data is completely secure."
        
        else:
            return "I'd be happy to help! Could you provide more details about what you're looking for? I can assist with broker connections, troubleshooting, pricing, or general questions about TradeSense."
    
    def _show_detailed_broker_guide(self, broker_key: str):
        """Show detailed broker setup guide."""
        st.subheader(f"📖 Detailed {broker_key.replace('_', ' ').title()} Setup Guide")
        
        # This would render comprehensive guides stored in documentation files
        st.info(f"Loading detailed guide for {broker_key}...")
        st.write("Detailed setup guide would be rendered here from documentation files.")


def render_help_center():
    """Main function to render help center."""
    help_center = HelpCenter()
    help_center.render_help_center()


if __name__ == "__main__":
    render_help_center()
