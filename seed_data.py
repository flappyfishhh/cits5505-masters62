import csv
import os
import sys

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, FileUpload, Upload

def seed():
    app = create_app()
    app.app_context().push()

    # Clean database
    db.drop_all()
    db.create_all()

    # Create users
    user1 = User(username='admin', email='admin@example.com')
    user1.set_password('admin')
    user1.set_security_answer('cookies')

    user2 = User(username='nancy', email='nancy@example.com')
    user2.set_password('nancy')
    user2.set_security_answer('earth')

    user3 = User(username='joshua', email='joshua@example.com')
    user3.set_password('joshua')
    user3.set_security_answer('mars')

    user4 = User(username='cham', email='cham@example.com')
    user4.set_password('cham')
    user4.set_security_answer('venus')

    user5 = User(username='ethan', email='ethan@example.com')
    user5.set_password('ethan')
    user5.set_security_answer('jupiter')

    db.session.add_all([user1, user2, user3, user4, user5])
    db.session.commit()

    # File info
    csv_files_info = [
        {
            'uploader': user1,
            'filename': 'IDCJAC0016_009021_1800_Data.csv',
            'city': 'PERTH',
            'latitude': -31.93,
            'longitude': 115.98,
            'visibility': 'private',
            'share_with': []
        },
        {
            'uploader': user1,
            'filename': 'IDCJAC0016_014015_1800_Data.csv',
            'city': 'DARWIN',
            'latitude': -12.42,
            'longitude': 130.89,
            'visibility': 'public',
            'share_with': []
        },
        {
            'uploader': user1,
            'filename': 'IDCJAC0016_023034_1800_Data.csv',
            'city': 'ADELAIDE',
            'latitude': -34.95,
            'longitude': 138.52,
            'visibility': 'shared',
            'share_with': [user2, user3, user4, user5]
        },
        {
            'uploader': user2,
            'filename': 'IDCJAC0016_086282_1800_Data.csv',
            'city': 'MELBOURNE',
            'latitude': -37.67,
            'longitude': 144.83,
            'visibility': 'private',
            'share_with': []
        },
        {
            'uploader': user3,
            'filename': 'IDCJAC0016_066024_1800_Data.csv',
            'city': 'SYDNEY',
            'latitude': -33.93,
            'longitude': 151.17,
            'visibility': 'private',
            'share_with': []
        },
        {
            'uploader': user4,
            'filename': 'IDCJAC0016_070351_1800_Data.csv',
            'city': 'CANBERRA',
            'latitude': -35.31,
            'longitude': 149.20,
            'visibility': 'private',
            'share_with': []
        },
        {
            'uploader': user5,
            'filename': 'IDCJAC0016_040913_1800_Data.csv',
            'city': 'BRISBANE',
            'latitude': -27.48,
            'longitude': 153.04,
            'visibility': 'private',
            'share_with': []
        }
    ]

    for file_info in csv_files_info:
        csv_path = os.path.join('tests', 'assets', file_info['filename'])

        file_upload = FileUpload(
            user_id=file_info['uploader'].id,
            filename=file_info['filename'],
            filepath=f'/uploads/{file_info["filename"]}',
            city=file_info['city'],
            latitude=file_info['latitude'],
            longitude=file_info['longitude'],
            visibility=file_info['visibility']
        )
        db.session.add(file_upload)
        db.session.commit()

        for shared_user in file_info.get('share_with', []):
            file_upload.share_with.append(shared_user)
        db.session.commit()

        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            uploads = [
                Upload(file_id=file_upload.id, row_number=i, data=row)
                for i, row in enumerate(reader, start=1)
            ]
            db.session.add_all(uploads)
            db.session.commit()

    print('Test data inserted successfully!')

if __name__ == '__main__':
    seed()
