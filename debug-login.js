const testAuth = async () => {
  console.log('🔍 Debugging Authentication Flow\n');

  // Test user data
  const testUser = {
    username: 'testuser789',
    email: 'test789@example.com',
    password: 'TestPass123!'
  };

  // Test 1: Try login with email field
  console.log('1️⃣ Testing login with email field:');
  try {
    const res1 = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testUser.email,
        password: testUser.password
      })
    });
    const data1 = await res1.json();
    console.log('Response:', res1.status, data1);
  } catch (err) {
    console.error('Error:', err);
  }

  // Test 2: Try login with username field
  console.log('\n2️⃣ Testing login with username field:');
  try {
    const res2 = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: testUser.username,
        password: testUser.password
      })
    });
    const data2 = await res2.json();
    console.log('Response:', res2.status, data2);
  } catch (err) {
    console.error('Error:', err);
  }

  // Test 3: Try login with both fields
  console.log('\n3️⃣ Testing login with both username and email:');
  try {
    const res3 = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: testUser.username,
        email: testUser.email,
        password: testUser.password
      })
    });
    const data3 = await res3.json();
    console.log('Response:', res3.status, data3);
  } catch (err) {
    console.error('Error:', err);
  }

  // Test 4: Check if user exists in database
  console.log('\n4️⃣ Checking if user was actually created:');
  // This would need a backend endpoint to verify, but let's try registration again
  try {
    const res4 = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'testuser2',
        email: 'test2@example.com',
        password: 'TestPass123!',
        confirm_password: 'TestPass123!'
      })
    });
    const data4 = await res4.json();
    console.log('Registration test:', res4.status, data4);
  } catch (err) {
    console.error('Error:', err);
  }

  // Test 5: Try login with email as username (what the frontend is doing)
  console.log('\n5️⃣ Testing login with email value in username field (frontend behavior):');
  try {
    const res5 = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: testUser.email,  // Sending email as username
        password: testUser.password
      })
    });
    const data5 = await res5.json();
    console.log('Response:', res5.status, data5);
  } catch (err) {
    console.error('Error:', err);
  }
};

testAuth();