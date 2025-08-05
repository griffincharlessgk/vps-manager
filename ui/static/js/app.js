// Gửi JWT token cho mọi fetch API (nếu có)
const _fetch = window.fetch;
window.fetch = function(url, opts={}) {
  return _fetch(url, opts);
};
// Ẩn/hiện nút thao tác theo quyền (nếu còn dùng)
function showAdminActions() {}
document.addEventListener('DOMContentLoaded', showAdminActions); 