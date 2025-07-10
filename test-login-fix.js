// Test the login fix
const testLoginFix = async () => {
  console.log('🧪 Testing Login Fix\n');

  // Test with the fixed frontend behavior
  console.log('Testing login with email field (fixed frontend behavior):');
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test789@example.com',
        password: 'TestPass123!'
      })
    });
    const data = await response.json();
    console.log('Response Status:', response.status);
    console.log('Response Data:', JSON.stringify(data, null, 2));
    
    if (response.status === 200) {
      console.log('\n✅ SUCCESS! Login is now working correctly!');
      console.log('Access Token:', data.access_token ? 'Received' : 'Missing');
      console.log('User Info:', {
        user_id: data.user_id,
        username: data.username,
        email: data.email
      });
    } else {
      console.log('\n❌ Login still failing');
    }
  } catch (err) {
    console.error('Error:', err.message);
  }
};

testLoginFix();