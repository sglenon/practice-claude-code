const { login } = require('./auth');
test('login succeeds for valid user', () => {
  expect(login('admin', 'admin123').success).toBe(true);
});
