// Test Frontend-Backend Connection
const testBackendConnection = async () => {
  console.log('🧪 Testing TradeSense API Connection...\n');

  // Test 1: Backend Health Check
  try {
    const healthResponse = await fetch('http://localhost:8000/api/health');
    console.log('✅ Backend Health Check:');
    console.log('   Status:', healthResponse.status);
    const healthData = await healthResponse.json();
    console.log('   Response:', JSON.stringify(healthData, null, 2));
  } catch (error) {
    console.error('❌ Backend unreachable:', error.message);
    console.log('⚠️  Make sure backend is running: cd src/backend && uvicorn main:app --reload');
    return;
  }

  // Test 2: API Docs
  try {
    const docsResponse = await fetch('http://localhost:8000/api/docs');
    console.log('\n📚 API Documentation:', docsResponse.status === 200 ? '✅ Available' : '❌ Not Found');
  } catch (error) {
    console.error('❌ Cannot reach API docs');
  }

  // Test 3: Login Endpoint
  try {
    const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'newuser@example.com',
        password: 'Password123!'
      })
    });
    console.log('\n🔐 Login Endpoint Test:');
    console.log('   Status:', loginResponse.status);
    const loginData = await loginResponse.json();
    console.log('   Response:', JSON.stringify(loginData, null, 2));
  } catch (error) {
    console.error('❌ Login endpoint error:', error.message);
  }

  // Test 4: CORS from browser origin
  try {
    const corsResponse = await fetch('http://localhost:8000/api/health', {
      headers: { 'Origin': 'http://localhost:3000' }
    });
    console.log('\n🌐 CORS Configuration:', corsResponse.status === 200 ? '✅ Properly configured' : '❌ May have issues');
  } catch (error) {
    console.error('❌ CORS check failed');
  }

  console.log('\n✨ Connection test complete!\n');
};

testBackendConnection();