function getSession() {
  return wx.getStorageSync("session") || null;
}

function isLoggedIn() {
  const session = getSession();
  return !!(session && session.userId);
}

function requireLogin() {
  if (!isLoggedIn()) {
    wx.navigateTo({ url: "/pages/auth/login/index" });
    return false;
  }
  return true;
}

module.exports = {
  getSession,
  isLoggedIn,
  requireLogin
};
