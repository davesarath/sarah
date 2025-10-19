CREATE DATABASE petcare;
USE petcare;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255) NOT NULL, -- hashed password
    email VARCHAR(100) UNIQUE,
    role ENUM('Admin','Veterinarian','Pet Owner') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE pets (
    pet_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    name VARCHAR(50),
    breed VARCHAR(50),
    age INT,
    gender ENUM('Male','Female'),
    medical_history TEXT,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id)
);
CREATE TABLE veterinarians (
    vet_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    specialization VARCHAR(100),
    phone VARCHAR(20),
    clinic_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    owner_id INT,
    vet_id INT,
    appointment_date DATETIME,
    status ENUM('Pending','Confirmed','Completed','Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id),
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id),
    FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id)
);
CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    vaccine_name VARCHAR(100),
    date_given DATE,
    next_due_date DATE,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)
);
CREATE TABLE medications (
    medication_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT,
    medicine_name VARCHAR(100),
    dosage VARCHAR(50),
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)
);
CREATE TABLE expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    pet_id INT,
    description VARCHAR(100),
    amount DECIMAL(10,2),
    date DATE,
    FOREIGN KEY (owner_id) REFERENCES owners(owner_id),
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)
);

describe users;
describe owners;
describe pets;
describe appointments;
describe expenses;
describe medications;
describe vaccinations;
describe veterinarians;
select * from users;
ALTER TABLE users
ADD COLUMN status ENUM('Active', 'Inactive');

INSERT INTO users (username, password, email, role, status)
VALUES 
('admin_user', 'hashed_admin_pass', 'admin@example.com', 'admin', 'Active'),
('vet_maya', 'hashed_vet_pass', 'maya@example.com', 'vet', 'Inactive');

DELETE FROM users WHERE username = 'vet_maya';

ALTER TABLE users 
MODIFY COLUMN role ENUM('Admin', 'Veterinarian', 'Pet Owner') NOT NULL;

ALTER TABLE users 
MODIFY COLUMN role ENUM('Admin', 'Veterinarian', 'Pet Owner') NOT NULL;

DELETE FROM users WHERE user_id > 0;

ALTER TABLE users AUTO_INCREMENT = 1;

ALTER TABLE users 
MODIFY COLUMN role ENUM('Admin', 'Veterinarian', 'Pet Owner') NOT NULL;