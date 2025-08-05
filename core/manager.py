from typing import Dict, List, Optional
from core.models import db, VPS, Account, BitLaunchAPI, BitLaunchVPS, ZingProxyAccount, ZingProxy, User
from datetime import datetime

def vps_to_dict(vps: VPS) -> dict:
    return {
        'id': vps.id,
        'service': vps.service,
        'name': vps.name,
        'ip': vps.ip,
        'expiry': vps.expiry
    }

def account_to_dict(acc: Account) -> dict:
    return {
        'id': acc.id,
        'service': acc.service,
        'username': acc.username,
        'expiry': acc.expiry
    }

def bitlaunch_api_to_dict(api: BitLaunchAPI) -> dict:
    return {
        'id': api.id,
        'email': api.email,
        'balance': api.balance,
        'limit': api.account_limit,
        'last_updated': api.last_updated.isoformat() if api.last_updated else None,
        'update_frequency': api.update_frequency,
        'is_active': api.is_active
    }

def bitlaunch_vps_to_dict(vps: BitLaunchVPS) -> dict:
    return {
        'id': vps.id,
        'server_id': vps.server_id,
        'name': vps.name,
        'status': vps.status,
        'ip_address': vps.ip_address,
        'location': vps.location,
        'plan': vps.plan,
        'created_at': vps.created_at.isoformat() if vps.created_at else None,
        'last_updated': vps.last_updated.isoformat() if vps.last_updated else None
    }

def clear_vps() -> None:
    VPS.query.delete()
    db.session.commit()

def add_vps(vps: dict) -> None:
    vps_obj = VPS(**vps)
    db.session.merge(vps_obj)
    db.session.commit()

def update_vps(vps_id: str, data: dict) -> None:
    vps = VPS.query.get(vps_id)
    if vps:
        for k, v in data.items():
            setattr(vps, k, v)
        db.session.commit()

def delete_vps(vps_id: str) -> None:
    vps = VPS.query.get(vps_id)
    if vps:
        db.session.delete(vps)
        db.session.commit()

def list_vps() -> List[dict]:
    return [vps_to_dict(v) for v in VPS.query.all()]

def get_vps_expiry(vps_id: str) -> Optional[str]:
    vps = VPS.query.get(vps_id)
    return vps.expiry if vps else None

def clear_accounts() -> None:
    Account.query.delete()
    db.session.commit()

def add_account(acc: dict) -> None:
    # Loại bỏ trường không có trong model
    acc = {k: v for k, v in acc.items() if k in ['id', 'service', 'username', 'expiry']}
    acc_obj = Account(**acc)
    db.session.merge(acc_obj)
    db.session.commit()

def update_account(acc_id: str, data: dict) -> None:
    acc = Account.query.get(acc_id)
    if acc:
        for k, v in data.items():
            setattr(acc, k, v)
        db.session.commit()

def delete_account(acc_id: str) -> None:
    acc = Account.query.get(acc_id)
    if acc:
        db.session.delete(acc)
        db.session.commit()

def list_accounts() -> List[dict]:
    return [account_to_dict(a) for a in Account.query.all()]

def get_account_expiry(acc_id: str) -> Optional[str]:
    acc = Account.query.get(acc_id)
    return acc.expiry if acc else None

# BitLaunch API management
def add_bitlaunch_api(user_id: int, email: str, api_key: str, update_frequency: int = 1) -> BitLaunchAPI:
    # Kiểm tra xem email đã tồn tại cho user này chưa
    existing = BitLaunchAPI.query.filter_by(user_id=user_id, email=email).first()
    if existing:
        # Cập nhật API key và thông tin khác
        existing.api_key = api_key
        existing.update_frequency = update_frequency
        existing.is_active = True
        db.session.commit()
        return existing
    
    # Tạo mới
    api = BitLaunchAPI(
        user_id=user_id,
        email=email,
        api_key=api_key,
        update_frequency=update_frequency
    )
    db.session.add(api)
    db.session.commit()
    return api

def update_bitlaunch_info(api_id: int, balance: float, limit: float) -> None:
    api = BitLaunchAPI.query.get(api_id)
    if api:
        api.balance = balance
        api.limit = limit
        api.last_updated = datetime.now()
        db.session.commit()

def list_bitlaunch_apis(user_id: int) -> List[dict]:
    apis = BitLaunchAPI.query.filter_by(user_id=user_id, is_active=True).all()
    return [bitlaunch_api_to_dict(api) for api in apis]

def delete_bitlaunch_api(api_id: int) -> None:
    api = BitLaunchAPI.query.get(api_id)
    if api:
        api.is_active = False  # Soft delete
        db.session.commit()

def get_bitlaunch_api_by_id(api_id: int) -> Optional[BitLaunchAPI]:
    return BitLaunchAPI.query.get(api_id)

def get_bitlaunch_apis_needing_update() -> List[BitLaunchAPI]:
    """Lấy danh sách API cần cập nhật theo tần suất"""
    now = datetime.now()
    apis = BitLaunchAPI.query.filter_by(is_active=True).all()
    need_update = []
    
    for api in apis:
        if not api.last_updated:
            need_update.append(api)
            continue
        
        days_since_update = (now - api.last_updated).days
        if days_since_update >= api.update_frequency:
            need_update.append(api)
    
    return need_update

# BitLaunch VPS management
def add_bitlaunch_vps(api_id: int, server_data: dict) -> BitLaunchVPS:
    """Thêm hoặc cập nhật VPS từ BitLaunch"""
    server_id = server_data.get('id')
    if not server_id:
        return None
    
    # Kiểm tra xem VPS đã tồn tại chưa
    existing = BitLaunchVPS.query.filter_by(api_id=api_id, server_id=server_id).first()
    if existing:
        # Cập nhật thông tin
        existing.name = server_data.get('name')
        existing.status = server_data.get('status')
        existing.ip_address = server_data.get('ip_address')
        existing.location = server_data.get('location')
        existing.plan = server_data.get('plan')
        existing.last_updated = datetime.now()
        db.session.commit()
        return existing
    
    # Tạo mới
    vps = BitLaunchVPS(
        api_id=api_id,
        server_id=server_id,
        name=server_data.get('name'),
        status=server_data.get('status'),
        ip_address=server_data.get('ip_address'),
        location=server_data.get('location'),
        plan=server_data.get('plan'),
        created_at=datetime.now(),
        last_updated=datetime.now()
    )
    db.session.add(vps)
    db.session.commit()
    return vps

def update_bitlaunch_vps_list(api_id: int, servers_list: List[dict]) -> None:
    """Cập nhật toàn bộ danh sách VPS cho một API"""
    # Xóa tất cả VPS cũ của API này
    BitLaunchVPS.query.filter_by(api_id=api_id).delete()
    
    # Thêm VPS mới
    for server in servers_list:
        add_bitlaunch_vps(api_id, server)
    
    db.session.commit()

def list_bitlaunch_vps(user_id: int) -> List[dict]:
    """Lấy danh sách VPS của user"""
    # Lấy tất cả API của user
    apis = BitLaunchAPI.query.filter_by(user_id=user_id, is_active=True).all()
    all_vps = []
    
    for api in apis:
        vps_list = BitLaunchVPS.query.filter_by(api_id=api.id).all()
        for vps in vps_list:
            vps_dict = bitlaunch_vps_to_dict(vps)
            vps_dict['email'] = api.email  # Thêm email để phân biệt
            all_vps.append(vps_dict)
    
    return all_vps

def delete_bitlaunch_vps(vps_id: int) -> None:
    """Xóa VPS"""
    vps = BitLaunchVPS.query.get(vps_id)
    if vps:
        db.session.delete(vps)
        db.session.commit()

def get_bitlaunch_vps_by_id(vps_id: int) -> Optional[BitLaunchVPS]:
    return BitLaunchVPS.query.get(vps_id) 

def zingproxy_account_to_dict(acc: ZingProxyAccount) -> dict:
    return {
        'id': acc.id,
        'email': acc.email,
        'balance': acc.balance,
        'created_at': acc.created_at.isoformat() if acc.created_at else None,
        'last_updated': acc.last_updated.isoformat() if acc.last_updated else None
    }

def zingproxy_to_dict(proxy: ZingProxy) -> dict:
    return {
        'id': proxy.id,
        'proxy_id': proxy.proxy_id,
        'ip': proxy.ip,
        'port': proxy.port,
        'port_socks5': proxy.port_socks5,
        'status': proxy.status,
        'expire_at': proxy.expire_at,
        'location': proxy.location,
        'type': proxy.type,
        'username': proxy.username,
        'password': proxy.password,
        'note': proxy.note,
        'created_at': proxy.created_at,
        'auto_renew': proxy.auto_renew,
        'link_change_ip': proxy.link_change_ip,
        'last_updated': proxy.last_updated.isoformat() if proxy.last_updated else None
    }

def add_zingproxy_account(user_id: int, email: str, access_token: str, balance: float, created_at: datetime, update_frequency: int = 1) -> ZingProxyAccount:
    existing = ZingProxyAccount.query.filter_by(user_id=user_id, email=email).first()
    now = datetime.now()
    if existing:
        existing.access_token = access_token
        existing.balance = balance
        existing.created_at = created_at
        existing.last_updated = now
        existing.update_frequency = update_frequency
        db.session.commit()
        return existing
    acc = ZingProxyAccount(
        user_id=user_id,
        email=email,
        access_token=access_token,
        balance=balance,
        created_at=created_at,
        last_updated=now,
        update_frequency=update_frequency
    )
    db.session.add(acc)
    db.session.commit()
    return acc

def update_zingproxy_account(acc_id: int, balance: float) -> None:
    acc = ZingProxyAccount.query.get(acc_id)
    if acc:
        acc.balance = balance
        acc.last_updated = datetime.now()
        db.session.commit()

def list_zingproxy_accounts(user_id: int) -> list:
    accs = ZingProxyAccount.query.filter_by(user_id=user_id).all()
    return [zingproxy_account_to_dict(a) for a in accs]

def delete_zingproxy_account(acc_id: int) -> None:
    acc = ZingProxyAccount.query.get(acc_id)
    if acc:
        db.session.delete(acc)
        db.session.commit()

def add_zingproxy(account_id: int, proxy_data: dict) -> ZingProxy:
    proxy_id = proxy_data.get('proxy_id')
    if not proxy_id:
        return None
    existing = ZingProxy.query.filter_by(account_id=account_id, proxy_id=proxy_id).first()
    now = datetime.now()
    if existing:
        existing.ip = proxy_data.get('ip')
        existing.port = proxy_data.get('port')
        existing.port_socks5 = proxy_data.get('port_socks5')
        existing.status = proxy_data.get('status')
        existing.expire_at = proxy_data.get('expire_at')
        existing.location = proxy_data.get('location')
        existing.type = proxy_data.get('type')
        existing.username = proxy_data.get('username')
        existing.password = proxy_data.get('password')
        existing.note = proxy_data.get('note')
        existing.created_at = proxy_data.get('created_at')
        existing.auto_renew = proxy_data.get('auto_renew')
        existing.link_change_ip = proxy_data.get('link_change_ip')
        existing.last_updated = now
        db.session.commit()
        return existing
    proxy = ZingProxy(
        account_id=account_id,
        proxy_id=proxy_id,
        ip=proxy_data.get('ip'),
        port=proxy_data.get('port'),
        port_socks5=proxy_data.get('port_socks5'),
        status=proxy_data.get('status'),
        expire_at=proxy_data.get('expire_at'),
        location=proxy_data.get('location'),
        type=proxy_data.get('type'),
        username=proxy_data.get('username'),
        password=proxy_data.get('password'),
        note=proxy_data.get('note'),
        created_at=proxy_data.get('created_at'),
        auto_renew=proxy_data.get('auto_renew'),
        link_change_ip=proxy_data.get('link_change_ip'),
        last_updated=now
    )
    db.session.add(proxy)
    db.session.commit()
    return proxy

def update_zingproxy_list(account_id: int, proxies: list) -> None:
    ZingProxy.query.filter_by(account_id=account_id).delete()
    for proxy in proxies:
        add_zingproxy(account_id, proxy)
    db.session.commit()

def list_zingproxies(account_id: int) -> list:
    proxies = ZingProxy.query.filter_by(account_id=account_id).all()
    return [zingproxy_to_dict(p) for p in proxies] 

def get_zingproxy_accounts_needing_update() -> list:
    now = datetime.now()
    accs = ZingProxyAccount.query.all()
    need_update = []
    for acc in accs:
        if not acc.last_updated:
            need_update.append(acc)
            continue
        days_since_update = (now - acc.last_updated).days
        if days_since_update >= (acc.update_frequency or 1):
            need_update.append(acc)
    return need_update 

def update_user_notify_hour(user_id: int, notify_hour: int) -> bool:
    """Cập nhật giờ gửi thông báo cho user"""
    try:
        user = User.query.get(user_id)
        if user:
            user.notify_hour = notify_hour
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Lỗi cập nhật notify_hour: {e}")
        return False

def get_user_notify_hour(user_id: int) -> int:
    """Lấy giờ gửi thông báo của user"""
    try:
        user = User.query.get(user_id)
        return user.notify_hour if user and user.notify_hour else 8
    except:
        return 8 