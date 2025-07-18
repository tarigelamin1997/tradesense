# Quick Start Guide - See the Stripe Integration in Action! 🚀

## Option 1: Use the Automated Script (Recommended)

```bash
# From the tradesense directory, run:
./start_servers.sh
```

This will:
- Activate the virtual environment
- Install dependencies
- Start both backend and frontend
- Show you all access URLs

## Option 2: Manual Start

### 1. Activate Virtual Environment
```bash
# Your virtual environment is called 'test_venv'
source test_venv/bin/activate

# You should see (test_venv) in your terminal prompt
```

### 2. Start Backend Server
```bash
# Terminal 1
cd src/backend
python main.py

# Backend will run at http://localhost:8000
# API docs at http://localhost:8000/api/docs
```

### 3. Start Frontend Server
```bash
# Terminal 2 (new terminal)
cd frontend
npm run dev

# Frontend will run at http://localhost:5173
```

### 4. (Optional) Start Stripe Webhook Listener
```bash
# Terminal 3 (if you have Stripe CLI)
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

## 🎯 What to Test

### 1. **Pricing Page** (http://localhost:5173/pricing)
- ✨ Beautiful pricing cards with "Most Popular" badge
- 🔄 Monthly/Yearly toggle with savings display
- 📱 Fully responsive design
- 🛡️ Trust badges and testimonials

### 2. **Checkout Flow**
- Click "Start Trading" on any plan
- See the enhanced checkout page with loading states
- Use test card: `4242 4242 4242 4242`
- Experience the confetti celebration!

### 3. **Usage Limits** (Free Plan)
- Create 8 trades → See 80% warning
- Create 9 trades → See 90% critical warning
- Try 11th trade → Get upgrade prompt

### 4. **Billing Portal** (http://localhost:5173/billing)
- View current plan and usage
- Visual progress bars
- Recent invoices
- One-click access to Stripe portal

### 5. **Feature Gates**
- Try accessing premium features
- See the enhanced upgrade prompts
- Test the smooth loading states

## 🧪 Test Cards

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

## ⚠️ Troubleshooting

### Virtual Environment Not Found?
```bash
# Create a new one
python3 -m venv test_venv
source test_venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use?
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### Missing Dependencies?
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## 📊 What's New in the Integration

1. **Enhanced Error Handling**
   - User-friendly error messages
   - Automatic retry with exponential backoff
   - Network failure recovery

2. **Smart Caching**
   - 30-second subscription cache
   - 10-60 second usage cache
   - Force refresh option

3. **Progressive Warnings**
   - 80% usage: Yellow warning
   - 90% usage: Red critical warning
   - 100% usage: Block with upgrade prompt

4. **Analytics Tracking**
   - Full conversion funnel
   - Usage milestones
   - Churn risk indicators

5. **Polished UX**
   - Smooth loading animations
   - Celebration confetti
   - Mobile responsive
   - Clear CTAs

Enjoy exploring the enhanced billing system! 🎉