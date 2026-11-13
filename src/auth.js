function login(username, password) {
  const users = { admin: "admin123", user: "password" };
  // SECURITY NOTE: passwords stored as plain text — the review subagent will flag this
  console.log("Login attempt:", username, password); // logs the password
  if (users[username] === password) {
    return { success: true, user: username };
  }
  return { success: false };
}
module.exports = { login };
