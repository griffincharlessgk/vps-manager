#!/usr/bin/env python3
"""
Script để thêm dữ liệu test cho VPS và Account
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from ui.app import create_app
from core.models import db, VPS, Account
from core.logging_config import setup_logging
import logging

def add_test_data():
    """Thêm dữ liệu test cho VPS và Account"""
    app = create_app()
    
    with app.app_context():
        # Setup logging
        setup_logging(app)
        logger = logging.getLogger(__name__)
        
        try:
            # Xóa dữ liệu cũ
            VPS.query.delete()
            Account.query.delete()
            db.session.commit()
            logger.info("Đã xóa dữ liệu cũ")
            
            # Thêm VPS test
            today = datetime.now()
            
            # VPS sắp hết hạn (3 ngày nữa)
            vps1 = VPS(
                id='vps-001',
                service='TestService',
                name='VPS Test 1',
                ip='192.168.1.100',
                expiry=(today + timedelta(days=3)).strftime('%Y-%m-%d')
            )
            
            # VPS hết hạn hôm nay
            vps2 = VPS(
                id='vps-002',
                service='TestService',
                name='VPS Test 2',
                ip='192.168.1.101',
                expiry=today.strftime('%Y-%m-%d')
            )
            
            # VPS hết hạn ngày mai
            vps3 = VPS(
                id='vps-003',
                service='TestService',
                name='VPS Test 3',
                ip='192.168.1.102',
                expiry=(today + timedelta(days=1)).strftime('%Y-%m-%d')
            )
            
            # VPS còn lâu mới hết hạn
            vps4 = VPS(
                id='vps-004',
                service='TestService',
                name='VPS Test 4',
                ip='192.168.1.103',
                expiry=(today + timedelta(days=30)).strftime('%Y-%m-%d')
            )
            
            db.session.add_all([vps1, vps2, vps3, vps4])
            
            # Thêm Account test
            # Account sắp hết hạn (2 ngày nữa)
            acc1 = Account(
                id='acc-001',
                service='TestAccount',
                username='testuser1',
                password='password123',
                expiry=(today + timedelta(days=2)).strftime('%Y-%m-%d')
            )
            
            # Account hết hạn hôm nay
            acc2 = Account(
                id='acc-002',
                service='TestAccount',
                username='testuser2',
                password='password456',
                expiry=today.strftime('%Y-%m-%d')
            )
            
            # Account còn lâu mới hết hạn
            acc3 = Account(
                id='acc-003',
                service='TestAccount',
                username='testuser3',
                password='password789',
                expiry=(today + timedelta(days=60)).strftime('%Y-%m-%d')
            )
            
            db.session.add_all([acc1, acc2, acc3])
            db.session.commit()
            
            logger.info("Đã thêm dữ liệu test thành công!")
            logger.info(f"- {len([vps1, vps2, vps3, vps4])} VPS")
            logger.info(f"- {len([acc1, acc2, acc3])} Account")
            
            # Hiển thị danh sách cảnh báo
            warnings = []
            for vps in [vps1, vps2, vps3, vps4]:
                if vps.expiry:
                    warnings.append(f"VPS '{vps.name}' sẽ hết hạn vào {vps.expiry}")
            
            for acc in [acc1, acc2, acc3]:
                if acc.expiry:
                    warnings.append(f"Account '{acc.username}' sẽ hết hạn vào {acc.expiry}")
            
            logger.info("Danh sách cảnh báo hết hạn:")
            for warning in warnings:
                logger.info(f"- {warning}")
            
        except Exception as e:
            logger.error(f"Lỗi thêm dữ liệu test: {e}")
            raise

if __name__ == '__main__':
    add_test_data() 