
import streamlit as st
from typing import Dict, List, Optional
import json
from datetime import datetime
from documentation.auto_support import AutoSupport
from logging_manager import log_info, LogCategory

class ChatbotSupport:
    """Intelligent chatbot for automated support."""
    
    def __init__(self):
        self.auto_support = AutoSupport()
        self.conversation_history = []
        self.knowledge_base = self._load_knowledge_base()
        self.escalation_triggers = [
            "speak to human", "human support", "not working", "still broken",
            "doesn't help", "frustrated", "urgent", "escalate"
        ]
    
    def _load_knowledge_base(self) -> Dict:
        """Load chatbot knowledge base."""
        return {
            "greetings": {
                "patterns": ["hello", "hi", "hey", "good morning", "good afternoon"],
                "responses": [
                    "Hello! I'm the TradeSense support bot. How can I help you today?",
                    "Hi there! I'm here to help with any TradeSense questions you have.",
                    "Welcome! I can assist with broker connections, troubleshooting, and general questions."
                ]
            },
            "broker_questions": {
                "patterns": ["broker", "connect", "integration", "sync", "account"],
                "responses": [
                    "I can help you connect to brokers! Which broker are you trying to connect to?",
                    "For broker connections, I'll need to know which platform you're using. Is it Interactive Brokers, TD Ameritrade, or another broker?"
                ]
            },
            "error_help": {
                "patterns": ["error", "problem", "issue", "broken", "not working", "failed"],
                "responses": [
                    "I'm sorry you're experiencing issues! Can you describe the specific error or problem?",
                    "Let me help troubleshoot that. What error message are you seeing?"
                ]
            },
            "pricing_questions": {
                "patterns": ["price", "cost", "billing", "subscription", "payment", "plan"],
                "responses": [
                    "Our pricing starts with a free Basic plan and $29/month for Pro. Would you like details on features?",
                    "We have flexible pricing options. The Basic plan is free, and Pro is $29/month with advanced features."
                ]
            },
            "security_questions": {
                "patterns": ["secure", "security", "safe", "privacy", "data protection"],
                "responses": [
                    "Security is our top priority! We use bank-level encryption and read-only access to your trading data.",
                    "Your data is completely secure. We never store passwords and use industry-standard encryption."
                ]
            }
        }
    
    def process_message(self, user_message: str, user_id: Optional[int] = None) -> Dict:
        """Process user message and generate response."""
        message_lower = user_message.lower()
        
        # Log the interaction
        log_info(
            f"Chatbot interaction: {user_message[:50]}...",
            details={"user_message": user_message, "user_id": user_id},
            category=LogCategory.USER_ACTION
        )
        
        # Check for escalation triggers
        if any(trigger in message_lower for trigger in self.escalation_triggers):
            return self._escalate_to_human(user_message)
        
        # Try auto-support first for technical issues
        auto_suggestion = self.auto_support.analyze_issue(user_description=user_message)
        if auto_suggestion and auto_suggestion.confidence > 0.7:
            return {
                "type": "auto_support",
                "response": f"I detected this might be a {auto_suggestion.title.lower()}. Here's what I recommend:",
                "suggestion": auto_suggestion,
                "confidence": auto_suggestion.confidence
            }
        
        # Use knowledge base for general questions
        best_response = self._find_knowledge_base_response(message_lower)
        if best_response:
            return {
                "type": "knowledge_base",
                "response": best_response,
                "follow_up": self._generate_follow_up(message_lower)
            }
        
        # Default response for unclear queries
        return {
            "type": "clarification",
            "response": "I'd be happy to help! Could you provide more details? I can assist with:",
            "options": [
                "🔗 Broker connections and integrations",
                "🔧 Technical troubleshooting",
                "💰 Pricing and subscription questions",
                "🔒 Security and privacy information",
                "📊 Features and capabilities"
            ]
        }
    
    def _find_knowledge_base_response(self, message: str) -> Optional[str]:
        """Find best response from knowledge base."""
        best_match = None
        best_score = 0
        
        for category, data in self.knowledge_base.items():
            score = 0
            for pattern in data["patterns"]:
                if pattern in message:
                    score += len(pattern)  # Longer matches get higher scores
            
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_match and best_score > 0:
            responses = self.knowledge_base[best_match]["responses"]
            # Return first response (could be randomized)
            return responses[0]
        
        return None
    
    def _generate_follow_up(self, message: str) -> Optional[str]:
        """Generate appropriate follow-up question."""
        if "broker" in message:
            return "Which specific broker are you trying to connect to?"
        elif "error" in message:
            return "What error message are you seeing exactly?"
        elif "price" in message:
            return "Are you interested in features comparison or have billing questions?"
        
        return None
    
    def _escalate_to_human(self, user_message: str) -> Dict:
        """Escalate conversation to human support."""
        ticket_id = f"CHAT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "type": "escalation",
            "response": "I understand you'd like to speak with a human. I've created a support ticket for you.",
            "ticket_id": ticket_id,
            "next_steps": "A support agent will contact you within 24 hours. Is there anything else I can help with in the meantime?"
        }
    
    def render_chatbot_widget(self):
        """Render chatbot widget in Streamlit."""
        st.subheader("🤖 TradeSense Support Bot")
        
        # Initialize chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": "Hello! I'm the TradeSense support bot. I can help with broker connections, troubleshooting, pricing questions, and more. How can I assist you today?",
                    "timestamp": datetime.now()
                }
            ]
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        
                        # Show additional elements for special response types
                        if message.get("type") == "auto_support":
                            self._render_auto_support_response(message)
                        elif message.get("type") == "escalation":
                            self._render_escalation_response(message)
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            })
            
            # Get bot response
            response_data = self.process_message(user_input)
            
            # Add bot response
            bot_message = {
                "role": "assistant",
                "content": response_data["response"],
                "timestamp": datetime.now(),
                "type": response_data.get("type"),
                "data": response_data
            }
            
            st.session_state.chat_messages.append(bot_message)
            
            # Show follow-up if available
            if response_data.get("follow_up"):
                follow_up_message = {
                    "role": "assistant", 
                    "content": response_data["follow_up"],
                    "timestamp": datetime.now()
                }
                st.session_state.chat_messages.append(follow_up_message)
            
            st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = st.session_state.chat_messages[:1]  # Keep initial message
            st.rerun()
    
    def _render_auto_support_response(self, message: Dict):
        """Render auto-support suggestion in chat."""
        suggestion = message["data"].get("suggestion")
        if suggestion:
            st.info(f"💡 **Quick Fix:** {suggestion.quick_fix}")
            
            with st.expander("📋 Detailed Steps"):
                for step in suggestion.detailed_solution:
                    st.write(step)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ This Helped", key=f"helpful_{message['timestamp']}"):
                    st.success("Great! Is there anything else I can help with?")
            
            with col2:
                if st.button("❌ Need More Help", key=f"more_help_{message['timestamp']}"):
                    self._escalate_to_human("Auto-suggestion didn't help")
    
    def _render_escalation_response(self, message: Dict):
        """Render escalation response in chat."""
        data = message.get("data", {})
        ticket_id = data.get("ticket_id")
        
        if ticket_id:
            st.success(f"**Ticket Created:** {ticket_id}")
            st.info("💬 A human agent will contact you within 24 hours")
    
    def render_floating_chat_button(self):
        """Render floating chat button for easy access."""
        # This would typically be rendered as a floating button
        # For Streamlit, we'll put it in the sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button("💬 Chat Support", type="primary"):
                st.session_state.show_chat = True
        
        # Show chat modal if requested
        if st.session_state.get("show_chat", False):
            with st.expander("💬 Support Chat", expanded=True):
                self.render_chatbot_widget()


def render_chatbot_support():
    """Main function to render chatbot support."""
    chatbot = ChatbotSupport()
    chatbot.render_chatbot_widget()

if __name__ == "__main__":
    render_chatbot_support()
