# Multi-Factor Authentication (MFA) Implementation

## Overview

TradeSense now supports Multi-Factor Authentication (MFA) to provide an additional layer of security for user accounts. The implementation supports multiple authentication methods and follows industry best practices.

## Supported Methods

1. **TOTP (Time-based One-Time Password)**
   - Compatible with Google Authenticator, Authy, 1Password, etc.
   - 6-digit codes that refresh every 30 seconds
   - Most secure and recommended method

2. **SMS Verification**
   - Codes sent via Twilio
   - 6-digit codes valid for 10 minutes
   - Requires phone number verification

3. **Email Verification**
   - Codes sent to registered email
   - 6-digit codes valid for 10 minutes
   - Backup method for all users

4. **Backup Codes**
   - 10 single-use recovery codes
   - Generated when MFA is first enabled
   - Can be regenerated at any time

## Technical Architecture

### Backend Components

1. **MFA Service** (`/src/backend/auth/mfa_service.py`)
   - Core MFA logic and verification
   - Encryption for TOTP secrets
   - Rate limiting and lockout protection
   - Device trust management

2. **API Endpoints** (`/src/backend/api/mfa.py`)
   - `/api/v1/mfa/status` - Get MFA status
   - `/api/v1/mfa/totp/setup` - Set up TOTP
   - `/api/v1/mfa/totp/verify` - Verify TOTP setup
   - `/api/v1/mfa/sms/setup` - Set up SMS
   - `/api/v1/mfa/sms/verify` - Verify SMS setup
   - `/api/v1/mfa/challenge` - Send MFA challenge
   - `/api/v1/mfa/verify` - Verify MFA code
   - `/api/v1/mfa/backup-codes/regenerate` - Regenerate backup codes
   - `/api/v1/mfa/disable` - Disable MFA
   - `/api/v1/mfa/trusted-devices` - Manage trusted devices

3. **Database Schema**
   - `mfa_devices` - Stores MFA device configurations
   - `mfa_backup_codes` - Stores hashed backup codes
   - `mfa_verification_codes` - Temporary verification codes
   - `mfa_auth_attempts` - Rate limiting and audit trail
   - `mfa_trusted_devices` - Trusted device management
   - `mfa_security_events` - Security event logging

### Frontend Components

1. **MFA Setup Component** (`/frontend/src/lib/components/MFASetup.svelte`)
   - Complete MFA configuration interface
   - QR code generation for TOTP
   - Phone number verification for SMS
   - Backup code display and download

2. **MFA Verification Component** (`/frontend/src/lib/components/MFAVerification.svelte`)
   - Login-time MFA verification
   - Method selection
   - Device trust options
   - Error handling and retries

3. **Security Settings Page** (`/frontend/src/routes/account/security/+page.svelte`)
   - MFA management dashboard
   - Trusted device management
   - Security recommendations

## User Flow

### Enabling MFA

1. User navigates to Account → Security Settings
2. Selects authentication method (TOTP recommended)
3. For TOTP:
   - Scans QR code with authenticator app
   - Enters verification code to confirm
   - Receives backup codes
4. For SMS:
   - Enters phone number
   - Receives and enters verification code
5. MFA is now active

### Login with MFA

1. User enters username and password
2. If MFA enabled, prompted for verification code
3. User selects method and enters code
4. Option to trust device for 30 days
5. Successful login

### Recovery Options

- **Lost Authenticator**: Use backup codes or SMS fallback
- **Lost Phone**: Use backup codes or email verification
- **No Backup Codes**: Contact support for identity verification

## Security Features

1. **Rate Limiting**
   - 5 failed attempts trigger 15-minute lockout
   - Per-user and per-IP tracking

2. **Encryption**
   - TOTP secrets encrypted at rest
   - Backup codes hashed with SHA-256

3. **Session Management**
   - MFA sessions expire after 10 minutes
   - Trusted devices expire after 30 days

4. **Audit Trail**
   - All MFA events logged
   - Security events tracked for monitoring

## Configuration

### Environment Variables

```bash
# Twilio Configuration (for SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# MFA Settings
MFA_TOTP_ISSUER=TradeSense
MFA_MAX_ATTEMPTS=5
MFA_LOCKOUT_MINUTES=15
MFA_TRUST_DEVICE_DAYS=30
```

### Database Migration

Run the migration to add MFA tables:

```bash
psql -U tradesense -d tradesense -f src/backend/migrations/add_mfa_tables.sql
```

## Monitoring

### Metrics

- `tradesense_mfa_setup_started_total` - MFA setup attempts
- `tradesense_mfa_enabled_total` - MFA enabled by method
- `tradesense_mfa_verifications_total` - Verification attempts
- `tradesense_mfa_codes_sent_total` - Codes sent by method
- `tradesense_backup_codes_used_total` - Backup code usage

### Admin Dashboard

View MFA statistics at `/admin/security`:
- Adoption rate
- Active methods breakdown
- Recent security events
- Failed authentication attempts

## Best Practices

1. **Encourage TOTP**: Most secure method, works offline
2. **Backup Codes**: Remind users to save securely
3. **Regular Reviews**: Users should review trusted devices
4. **Support Training**: Staff should understand recovery procedures

## Troubleshooting

### Common Issues

1. **TOTP Code Invalid**
   - Check device time synchronization
   - Verify correct app entry
   - Try adjacent time windows

2. **SMS Not Received**
   - Verify phone number format
   - Check Twilio logs
   - Try email fallback

3. **Rate Limited**
   - Wait 15 minutes
   - Use backup codes
   - Contact support if urgent

### Support Procedures

1. **Identity Verification**: Multiple data points required
2. **MFA Reset**: Requires supervisor approval
3. **Audit Trail**: Document all support actions

## Future Enhancements

1. **Hardware Keys**: FIDO2/WebAuthn support
2. **Biometric Authentication**: Face/Touch ID
3. **Push Notifications**: App-based approval
4. **Risk-Based Authentication**: Adaptive MFA requirements