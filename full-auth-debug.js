const fullAuthDebug = async () => {
  console.log('🔍 Full Authentication Debug\n');
  
  // Generate unique test data
  const timestamp = Date.now();
  const testData = {
    username: `debuguser${timestamp}`,
    email: `debug${timestamp}@test.com`,
    password: 'DebugPass123!'
  };
  
  console.log('Test data:', testData);
  
  // Step 1: Test if backend is reachable
  console.log('\n1️⃣ Testing backend connection:');
  try {
    const health = await fetch('http://localhost:8000/api/health');
    console.log('Health check:', health.status);
  } catch (err) {
    console.error('❌ Backend not reachable!', err.message);
    return;
  }
  
  // Step 2: Test registration with detailed error info
  console.log('\n2️⃣ Testing registration:');
  try {
    const regResponse = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: testData.username,
        email: testData.email,
        password: testData.password,
        confirm_password: testData.password
      })
    });
    
    const regText = await regResponse.text();
    console.log('Registration status:', regResponse.status);
    console.log('Registration response:', regText);
    
    try {
      const regData = JSON.parse(regText);
      console.log('Parsed response:', regData);
    } catch {
      console.log('Response is not JSON');
    }
  } catch (err) {
    console.error('Registration error:', err);
  }
  
  // Step 3: Test login with the same credentials
  console.log('\n3️⃣ Testing login with email:');
  try {
    const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testData.email,
        password: testData.password
      })
    });
    
    const loginText = await loginResponse.text();
    console.log('Login status:', loginResponse.status);
    console.log('Login response:', loginText);
  } catch (err) {
    console.error('Login error:', err);
  }
  
  // Step 4: Check what the frontend is actually sending
  console.log('\n4️⃣ Testing exact frontend request format:');
  // Simulate exact frontend request
  try {
    const frontendRequest = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    });
    
    console.log('Frontend-style request status:', frontendRequest.status);
    const responseText = await frontendRequest.text();
    console.log('Response:', responseText);
  } catch (err) {
    console.error('Frontend-style request error:', err);
  }
};

fullAuthDebug();