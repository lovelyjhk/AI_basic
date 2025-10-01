"""
의료 데이터 시뮬레이터 및 랜섬웨어 행위 모방
석사 논문용 MVP
"""

import os
import time
import random
import string
import csv
import threading
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalDataSimulator:
    """의료 데이터 생성기 (EMR/PACS 시뮬레이션)"""
    
    def __init__(self, data_dir: str = "simulation_data/medical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_patient_record(self, patient_id: int) -> Dict:
        """환자 레코드 생성"""
        first_names = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임']
        last_names = ['민수', '영희', '철수', '수진', '지훈', '현아', '동욱', '서연', '준호', '미나']
        
        return {
            'patient_id': f'P{patient_id:08d}',
            'name': random.choice(first_names) + random.choice(last_names),
            'age': random.randint(1, 90),
            'gender': random.choice(['M', 'F']),
            'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
            'diagnosis': random.choice([
                'Hypertension', 'Diabetes', 'Asthma', 'Cancer', 'Heart Disease',
                'Stroke', 'Pneumonia', 'COVID-19', 'Fracture', 'Surgery'
            ]),
            'admission_date': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
            'room_number': f'{random.randint(1,5)}{random.randint(0,9)}{random.randint(0,9)}',
            'attending_physician': f'Dr. {random.choice(["Smith", "Lee", "Kim", "Park", "Johnson"])}',
            'emergency_contact': f'010-{random.randint(1000,9999)}-{random.randint(1000,9999)}',
        }
    
    def generate_patient_dataset(self, num_patients: int = 100000) -> str:
        """대규모 환자 데이터셋 생성"""
        output_file = self.data_dir / f'patients_{num_patients}.csv'
        
        logger.info(f"{num_patients}명의 환자 데이터 생성 중...")
        start_time = time.time()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = None
            for i in range(1, num_patients + 1):
                record = self.generate_patient_record(i)
                
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=record.keys())
                    writer.writeheader()
                
                writer.writerow(record)
                
                if i % 10000 == 0:
                    logger.info(f"  진행: {i}/{num_patients} ({i/num_patients*100:.1f}%)")
        
        elapsed = time.time() - start_time
        logger.info(f"환자 데이터 생성 완료: {output_file} ({elapsed:.2f}초)")
        
        return str(output_file)
    
    def generate_medical_images(self, num_images: int = 1000, image_size_kb: int = 512) -> List[str]:
        """의료 영상 파일 생성 (PACS 시뮬레이션)"""
        images_dir = self.data_dir / 'images'
        images_dir.mkdir(exist_ok=True)
        
        logger.info(f"{num_images}개의 의료 영상 생성 중...")
        
        created_files = []
        data = os.urandom(image_size_kb * 1024)
        
        for i in range(1, num_images + 1):
            filename = images_dir / f'DICOM_{i:06d}.dcm'
            with open(filename, 'wb') as f:
                f.write(data)
            created_files.append(str(filename))
            
            if i % 100 == 0:
                logger.info(f"  진행: {i}/{num_images}")
        
        logger.info(f"의료 영상 생성 완료")
        return created_files
    
    def simulate_normal_operations(self, duration_sec: int = 60):
        """정상 의료 운영 시뮬레이션 (낮은 파일 수정 빈도)"""
        logger.info(f"정상 운영 시뮬레이션 시작 ({duration_sec}초)")
        
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration_sec:
            # 1-2초마다 파일 수정
            time.sleep(random.uniform(1, 2))
            
            # 랜덤 환자 레코드 수정
            patient_id = random.randint(1, 1000)
            record_file = self.data_dir / f'patient_{patient_id}.txt'
            
            with open(record_file, 'w') as f:
                f.write(f"Patient {patient_id} - Updated at {time.time()}\n")
            
            operations += 1
        
        logger.info(f"정상 운영 종료: {operations}회 작업 수행")
        return operations


class RansomwareSimulator:
    """랜섬웨어 행위 시뮬레이터"""
    
    def __init__(self, target_dir: str = "simulation_data/medical"):
        self.target_dir = Path(target_dir)
        self.is_attacking = False
        self.attack_thread = None
    
    def simulate_precursor_behavior(self, duration_sec: int = 30):
        """
        랜섬웨어 전조 증상 시뮬레이션
        - 점진적으로 파일 수정 빈도 증가
        - 의심스러운 프로세스 활동 증가
        """
        logger.info(f"랜섬웨어 전조 증상 시뮬레이션 시작 ({duration_sec}초)")
        
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration_sec:
            elapsed = time.time() - start_time
            progress = elapsed / duration_sec
            
            # 점진적으로 파일 수정 빈도 증가 (0.5초 -> 0.1초)
            sleep_time = 0.5 - (0.4 * progress)
            time.sleep(max(0.1, sleep_time))
            
            # 파일 읽기 (reconnaissance)
            test_file = self.target_dir / 'patients_100000.csv'
            if test_file.exists():
                with open(test_file, 'r') as f:
                    _ = f.read(1024)  # 일부만 읽기
            
            operations += 1
        
        logger.info(f"전조 증상 시뮬레이션 종료: {operations}회 작업")
        return operations
    
    def simulate_encryption_attack(self, duration_sec: int = 10, files_per_sec: int = 100):
        """
        랜섬웨어 본격 암호화 공격 시뮬레이션
        - 초당 100개 이상의 파일 수정
        - 파일 내용을 랜덤 데이터로 덮어쓰기 (암호화 모방)
        """
        logger.info(f"랜섬웨어 암호화 공격 시뮬레이션 시작")
        logger.warning(f"!!! 위험: {duration_sec}초 동안 초당 {files_per_sec}개 파일 수정 !!!")
        
        self.is_attacking = True
        start_time = time.time()
        encrypted_count = 0
        
        try:
            while time.time() - start_time < duration_sec and self.is_attacking:
                batch_start = time.time()
                
                # 1초 동안 files_per_sec개 파일 수정
                for i in range(files_per_sec):
                    if not self.is_attacking:
                        break
                    
                    # 타겟 파일 선택
                    target_file = self.target_dir / f'encrypted_{encrypted_count}.enc'
                    
                    # 랜덤 데이터로 덮어쓰기 (암호화 모방)
                    encrypted_data = os.urandom(random.randint(1024, 10240))
                    with open(target_file, 'wb') as f:
                        f.write(encrypted_data)
                    
                    encrypted_count += 1
                
                # 1초 맞추기
                batch_elapsed = time.time() - batch_start
                if batch_elapsed < 1.0:
                    time.sleep(1.0 - batch_elapsed)
                
                logger.info(f"암호화 진행: {encrypted_count}개 파일 (경과: {time.time()-start_time:.1f}초)")
        
        finally:
            self.is_attacking = False
            logger.info(f"암호화 공격 종료: 총 {encrypted_count}개 파일 수정")
        
        return encrypted_count
    
    def start_attack_async(self, delay_sec: int = 5, attack_duration: int = 10):
        """비동기 공격 시작 (백그라운드 스레드)"""
        def attack_worker():
            logger.info(f"{delay_sec}초 후 공격 시작...")
            time.sleep(delay_sec)
            self.simulate_encryption_attack(duration_sec=attack_duration)
        
        self.attack_thread = threading.Thread(target=attack_worker, daemon=True)
        self.attack_thread.start()
        logger.info("백그라운드 공격 스레드 시작")
    
    def stop_attack(self):
        """공격 중지"""
        self.is_attacking = False
        if self.attack_thread:
            self.attack_thread.join(timeout=2)
        logger.info("공격 중지됨")


class IntegratedSimulation:
    """통합 시뮬레이션 (정상 운영 + 랜섬웨어 공격)"""
    
    def __init__(self, data_dir: str = "simulation_data"):
        self.data_dir = Path(data_dir)
        self.medical_sim = MedicalDataSimulator(str(self.data_dir / 'medical'))
        self.ransomware_sim = RansomwareSimulator(str(self.data_dir / 'medical'))
    
    def setup_environment(self, num_patients: int = 100000, num_images: int = 1000):
        """환경 설정 (의료 데이터 생성)"""
        logger.info("=== 시뮬레이션 환경 설정 ===")
        
        # 환자 데이터 생성
        patient_file = self.medical_sim.generate_patient_dataset(num_patients)
        
        # 의료 영상 생성
        image_files = self.medical_sim.generate_medical_images(num_images)
        
        logger.info(f"환경 설정 완료: 환자 {num_patients}명, 영상 {num_images}개")
        
        return patient_file, image_files
    
    def run_full_scenario(self):
        """
        전체 시나리오 실행
        1. 정상 운영 (30초)
        2. 랜섬웨어 전조 증상 (30초)
        3. 본격 공격 (10초)
        """
        logger.info("\n" + "="*60)
        logger.info("통합 시뮬레이션 시작")
        logger.info("="*60 + "\n")
        
        # Phase 1: 정상 운영
        logger.info("Phase 1: 정상 운영")
        self.medical_sim.simulate_normal_operations(duration_sec=30)
        
        time.sleep(2)
        
        # Phase 2: 전조 증상
        logger.info("\nPhase 2: 랜섬웨어 전조 증상")
        self.ransomware_sim.simulate_precursor_behavior(duration_sec=30)
        
        time.sleep(2)
        
        # Phase 3: 본격 공격
        logger.info("\nPhase 3: 랜섬웨어 본격 공격")
        encrypted_count = self.ransomware_sim.simulate_encryption_attack(
            duration_sec=10,
            files_per_sec=100
        )
        
        logger.info(f"\n시뮬레이션 종료: {encrypted_count}개 파일 영향")


if __name__ == "__main__":
    # 통합 시뮬레이션 실행
    sim = IntegratedSimulation()
    
    # 환경 설정 (처음 한 번만)
    if not (Path("simulation_data/medical/patients_100000.csv")).exists():
        sim.setup_environment(num_patients=100000, num_images=1000)
    
    # 전체 시나리오 실행
    sim.run_full_scenario()
