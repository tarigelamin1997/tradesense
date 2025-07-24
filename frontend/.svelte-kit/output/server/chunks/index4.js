const app = {
  name: "TradeSense",
  tagline: "Smart Trading, Better Decisions"
};
const nav = {
  dashboard: "Dashboard",
  trades: "Trade Log",
  portfolio: "Portfolio",
  analytics: "Analytics",
  journal: "Journal",
  playbook: "Playbook",
  aiInsights: "AI Insights",
  "import": "Import",
  settings: "Settings",
  logout: "Logout",
  login: "Login",
  register: "Sign Up",
  profile: "Profile",
  billing: "Billing",
  support: "Support"
};
const actions$1 = {
  save: "Save",
  cancel: "Cancel",
  "delete": "Delete",
  edit: "Edit",
  create: "Create",
  update: "Update",
  submit: "Submit",
  confirm: "Confirm",
  back: "Back",
  next: "Next",
  previous: "Previous",
  close: "Close",
  search: "Search",
  filter: "Filter",
  sort: "Sort",
  "export": "Export",
  "import": "Import",
  download: "Download",
  upload: "Upload",
  refresh: "Refresh",
  retry: "Retry",
  loading: "Loading...",
  processing: "Processing..."
};
const status$1 = {
  success: "Success",
  error: "Error",
  warning: "Warning",
  info: "Info",
  pending: "Pending",
  active: "Active",
  inactive: "Inactive",
  online: "Online",
  offline: "Offline",
  connected: "Connected",
  disconnected: "Disconnected"
};
const time = {
  today: "Today",
  yesterday: "Yesterday",
  tomorrow: "Tomorrow",
  thisWeek: "This Week",
  lastWeek: "Last Week",
  thisMonth: "This Month",
  lastMonth: "Last Month",
  thisYear: "This Year",
  lastYear: "Last Year",
  custom: "Custom",
  from: "From",
  to: "To",
  date: "Date",
  time: "Time",
  dateTime: "Date & Time"
};
const pagination = {
  showing: "Showing {{from}} to {{to}} of {{total}}",
  page: "Page {{current}} of {{total}}",
  itemsPerPage: "Items per page",
  first: "First",
  last: "Last"
};
const errors = {
  general: "Something went wrong. Please try again.",
  network: "Network error. Please check your connection.",
  notFound: "Page not found",
  unauthorized: "You are not authorized to view this page",
  forbidden: "Access forbidden",
  serverError: "Server error. Please try again later.",
  timeout: "Request timed out. Please try again."
};
const confirmation = {
  title: "Are you sure?",
  deleteMessage: "This action cannot be undone.",
  logoutMessage: "Are you sure you want to log out?"
};
const common = {
  app,
  nav,
  actions: actions$1,
  status: status$1,
  time,
  pagination,
  errors,
  confirmation
};
const login = {
  title: "Welcome Back",
  subtitle: "Sign in to your TradeSense account",
  email: "Email or Username",
  emailPlaceholder: "Enter your email or username",
  password: "Password",
  passwordPlaceholder: "Enter your password",
  rememberMe: "Remember me",
  forgotPassword: "Forgot password?",
  submit: "Sign In",
  submitting: "Signing in...",
  noAccount: "Don't have an account?",
  signUp: "Sign up",
  or: "Or",
  continueWith: "Continue with {{provider}}",
  errors: {
    invalidCredentials: "Invalid email or password",
    accountLocked: "Account is locked. Please contact support.",
    tooManyAttempts: "Too many login attempts. Please try again later."
  }
};
const register = {
  title: "Create Account",
  subtitle: "Join TradeSense and start trading smarter",
  name: "Full Name",
  namePlaceholder: "Enter your full name",
  email: "Email",
  emailPlaceholder: "Enter your email",
  username: "Username",
  usernamePlaceholder: "Choose a username",
  password: "Password",
  passwordPlaceholder: "Create a password",
  confirmPassword: "Confirm Password",
  confirmPasswordPlaceholder: "Confirm your password",
  terms: "I agree to the Terms of Service and Privacy Policy",
  submit: "Create Account",
  submitting: "Creating account...",
  hasAccount: "Already have an account?",
  signIn: "Sign in",
  errors: {
    emailTaken: "Email is already registered",
    usernameTaken: "Username is already taken",
    weakPassword: "Password is too weak",
    passwordMismatch: "Passwords do not match"
  }
};
const forgotPassword = {
  title: "Forgot Password",
  subtitle: "Enter your email to reset your password",
  email: "Email",
  emailPlaceholder: "Enter your email",
  submit: "Send Reset Link",
  submitting: "Sending...",
  backToLogin: "Back to login",
  success: "Check your email for reset instructions",
  errors: {
    emailNotFound: "Email not found"
  }
};
const resetPassword = {
  title: "Reset Password",
  subtitle: "Create a new password",
  newPassword: "New Password",
  newPasswordPlaceholder: "Enter new password",
  confirmPassword: "Confirm Password",
  confirmPasswordPlaceholder: "Confirm new password",
  submit: "Reset Password",
  submitting: "Resetting...",
  success: "Password reset successfully",
  errors: {
    invalidToken: "Invalid or expired reset token",
    passwordMismatch: "Passwords do not match"
  }
};
const changePassword = {
  title: "Change Password",
  currentPassword: "Current Password",
  currentPasswordPlaceholder: "Enter current password",
  newPassword: "New Password",
  newPasswordPlaceholder: "Enter new password",
  confirmPassword: "Confirm Password",
  confirmPasswordPlaceholder: "Confirm new password",
  submit: "Change Password",
  submitting: "Changing...",
  success: "Password changed successfully",
  errors: {
    incorrectPassword: "Current password is incorrect",
    samePassword: "New password must be different"
  }
};
const mfa = {
  title: "Two-Factor Authentication",
  subtitle: "Enter the code from your authenticator app",
  code: "Verification Code",
  codePlaceholder: "Enter 6-digit code",
  submit: "Verify",
  submitting: "Verifying...",
  useBackup: "Use backup code",
  errors: {
    invalidCode: "Invalid verification code",
    expiredCode: "Code has expired"
  }
};
const logout = {
  message: "You have been logged out successfully",
  redirect: "Redirecting to login..."
};
const auth = {
  login,
  register,
  forgotPassword,
  resetPassword,
  changePassword,
  mfa,
  logout
};
const required = "{{field}} is required";
const email = "Please enter a valid email address";
const minLength = "{{field}} must be at least {{min}} characters";
const maxLength = "{{field}} must not exceed {{max}} characters";
const minValue = "{{field}} must be at least {{min}}";
const maxValue = "{{field}} must not exceed {{max}}";
const pattern = "{{field}} format is invalid";
const passwordStrength = {
  weak: "Password is too weak",
  medium: "Password strength is medium",
  strong: "Password is strong"
};
const passwordRequirements = {
  minLength: "At least 8 characters",
  uppercase: "One uppercase letter",
  lowercase: "One lowercase letter",
  number: "One number",
  special: "One special character"
};
const match = "{{field}} must match {{otherField}}";
const unique = "{{field}} must be unique";
const date = {
  invalid: "Invalid date",
  future: "Date must be in the future",
  past: "Date must be in the past",
  between: "Date must be between {{start}} and {{end}}"
};
const number = {
  invalid: "Invalid number",
  integer: "Must be a whole number",
  positive: "Must be a positive number",
  negative: "Must be a negative number"
};
const file = {
  required: "Please select a file",
  size: "File size must not exceed {{max}}",
  type: "Invalid file type. Allowed: {{types}}"
};
const trades$1 = {
  symbol: "Symbol is required",
  quantity: "Quantity must be greater than 0",
  price: "Price must be greater than 0",
  entryPrice: "Entry price is required",
  exitPrice: "Exit price is required",
  stopLoss: "Stop loss must be less than entry price",
  takeProfit: "Take profit must be greater than entry price"
};
const validation = {
  required,
  email,
  minLength,
  maxLength,
  minValue,
  maxValue,
  pattern,
  passwordStrength,
  passwordRequirements,
  match,
  unique,
  date,
  number,
  file,
  trades: trades$1
};
const title$1 = "Dashboard";
const welcome = "Welcome back, {{name}}!";
const overview = "Overview";
const recentActivity = "Recent Activity";
const quickActions = "Quick Actions";
const metrics = {
  totalTrades: "Total Trades",
  winRate: "Win Rate",
  profitLoss: "Profit/Loss",
  avgReturn: "Avg Return",
  totalVolume: "Total Volume",
  activeTrades: "Active Trades",
  todaysPL: "Today's P/L",
  weeklyPL: "Weekly P/L",
  monthlyPL: "Monthly P/L",
  yearlyPL: "Yearly P/L"
};
const charts = {
  performanceOverTime: "Performance Over Time",
  profitByStrategy: "Profit by Strategy",
  winLossDistribution: "Win/Loss Distribution",
  riskRewardRatio: "Risk/Reward Ratio",
  tradingVolume: "Trading Volume",
  topPerformers: "Top Performers",
  worstPerformers: "Worst Performers"
};
const widgets = {
  recentTrades: "Recent Trades",
  upcomingAlerts: "Upcoming Alerts",
  marketOverview: "Market Overview",
  newsAndAnalysis: "News & Analysis",
  openPositions: "Open Positions",
  watchlist: "Watchlist"
};
const empty = {
  noData: "No data available",
  noTrades: "No trades yet. Start by adding your first trade!",
  noAlerts: "No alerts set",
  noPositions: "No open positions"
};
const timeframes = {
  "1d": "1 Day",
  "1w": "1 Week",
  "1m": "1 Month",
  "3m": "3 Months",
  "6m": "6 Months",
  "1y": "1 Year",
  ytd: "YTD",
  all: "All Time"
};
const dashboard = {
  title: title$1,
  welcome,
  overview,
  recentActivity,
  quickActions,
  metrics,
  charts,
  widgets,
  empty,
  timeframes
};
const title = "Trade Log";
const newTrade = "New Trade";
const editTrade = "Edit Trade";
const deleteTrade = "Delete Trade";
const importTrades = "Import Trades";
const exportTrades = "Export Trades";
const fields = {
  symbol: "Symbol",
  side: "Side",
  quantity: "Quantity",
  entryPrice: "Entry Price",
  exitPrice: "Exit Price",
  entryDate: "Entry Date",
  exitDate: "Exit Date",
  stopLoss: "Stop Loss",
  takeProfit: "Take Profit",
  commission: "Commission",
  fees: "Fees",
  notes: "Notes",
  tags: "Tags",
  strategy: "Strategy",
  status: "Status",
  pnl: "P&L",
  returnPercent: "Return %",
  riskReward: "Risk/Reward"
};
const side = {
  buy: "Buy",
  sell: "Sell",
  long: "Long",
  short: "Short"
};
const status = {
  open: "Open",
  closed: "Closed",
  pending: "Pending",
  cancelled: "Cancelled",
  partial: "Partial"
};
const filters = {
  all: "All Trades",
  open: "Open Trades",
  closed: "Closed Trades",
  winners: "Winners",
  losers: "Losers",
  today: "Today",
  thisWeek: "This Week",
  thisMonth: "This Month",
  dateRange: "Date Range",
  symbol: "By Symbol",
  strategy: "By Strategy"
};
const actions = {
  view: "View Details",
  edit: "Edit",
  "delete": "Delete",
  duplicate: "Duplicate",
  close: "Close Trade",
  addToJournal: "Add to Journal"
};
const summary = {
  totalTrades: "Total Trades",
  openTrades: "Open Trades",
  closedTrades: "Closed Trades",
  totalPnl: "Total P&L",
  winRate: "Win Rate",
  avgWin: "Avg Win",
  avgLoss: "Avg Loss",
  profitFactor: "Profit Factor"
};
const messages = {
  tradeAdded: "Trade added successfully",
  tradeUpdated: "Trade updated successfully",
  tradeDeleted: "Trade deleted successfully",
  tradeClosed: "Trade closed successfully",
  importSuccess: "{{count}} trades imported successfully",
  exportSuccess: "Trades exported successfully",
  deleteConfirm: "Are you sure you want to delete this trade?"
};
const trades = {
  title,
  newTrade,
  editTrade,
  deleteTrade,
  importTrades,
  exportTrades,
  fields,
  side,
  status,
  filters,
  actions,
  summary,
  messages
};
const index = {
  common,
  auth,
  validation,
  dashboard,
  trades
};
export {
  index as default
};
