CREATE DATABASE IF NOT EXISTS yogo;
use yogo;
DROP TABLE IF EXISTS replies;
DROP TABLE IF EXISTS support_requests;
DROP TABLE IF EXISTS event_images;
DROP TABLE IF EXISTS `changes`;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS journals;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS user_subscriptions;
DROP TABLE IF EXISTS subscription_plans;
DROP TABLE IF EXISTS users;
CREATE TABLE `users` (
    `user_id` int NOT NULL AUTO_INCREMENT,
    `username` varchar(20) NOT NULL,
    `password_hash` char(60) BINARY NOT NULL COMMENT 'Bcrypt Password Hash and Salt (60 bytes)',
    `email` varchar(320) NOT NULL COMMENT 'Maximum email address length according to RFC5321 section 4.5.3.1 is 320 characters (64 for local-part, 1 for at sign, 255 for domain)',
    `first_name` varchar(50) NOT NULL,
    `last_name` varchar(50) NOT NULL,
    `location` varchar(50) NOT NULL,
    `profile_image` varchar(255) DEFAULT 'default.png',
    `role` enum('traveller', 'editor', 'admin') NOT NULL DEFAULT 'traveller',
    `user_status` enum('active', 'ban_share', 'ban_all') NOT NULL DEFAULT 'active',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `username` (`username`)
);
CREATE TABLE `journals`(
    `journal_id` int NOT NULL AUTO_INCREMENT,
    `j_title` varchar(255) NOT NULL,
    `j_description` text NOT NULL,
    `j_startdate` DATE NOT NULL,
    `j_status` enum('public', 'private') NOT NULL DEFAULT 'private',
    `j_published` enum('yes', 'no') NOT NULL DEFAULT 'no',
    `user_id` int NOT NULL,
    Foreign key (`user_id`) references `users`(`user_id`) ON DELETE CASCADE,
    `user_status` enum('active', 'ban_share', 'ban_all') NOT NULL DEFAULT 'active',
    PRIMARY KEY (`journal_id`)
);
CREATE TABLE `events`(
    `event_id` int NOT NULL AUTO_INCREMENT,
    `e_title` varchar(255) NOT NULL,
    `e_description` text NOT NULL,
    `e_startdatetime` DATETIME NOT NULL,
    `e_enddatetime` DATETIME,
    `e_location` varchar(50) NOT NULL,
    `e_image` varchar(255),
    `journal_id` int NOT NULL,
    Foreign key (`journal_id`) references `journals`(`journal_id`) ON DELETE CASCADE,
    PRIMARY KEY (`event_id`)
);
CREATE TABLE `changes`(
    `change_id` int NOT NULL AUTO_INCREMENT,
    `new_location` varchar(50) NOT NULL,
    `changed_date` TIMESTAMP NOT NULL,
    `changed_by` int NOT NULL,
    `event_id` int NOT NULL,
    Foreign key (`changed_by`) references `users`(`user_id`) ON DELETE CASCADE,
    Foreign key (`event_id`) references `events`(`event_id`) ON DELETE CASCADE,
    PRIMARY KEY (`change_id`)
);
use yogo;
CREATE TABLE subscription_plans (
    plan_name VARCHAR(50) PRIMARY KEY,
    months INT NOT NULL,
    price_excl_gst DECIMAL(10, 2),
    price_incl_gst DECIMAL(10, 2),
    discount_percent VARCHAR(10),
    is_free_trial TINYINT(1) DEFAULT 0,
    is_admin_grant TINYINT(1) DEFAULT 0
);
CREATE TABLE user_subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_by_admin INT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_name) REFERENCES subscription_plans(plan_name) ON DELETE CASCADE,
    FOREIGN KEY (created_by_admin) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    card_last4 CHAR(4),
    billing_country VARCHAR(100),
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(subscription_id) ON DELETE CASCADE
);
ALTER TABLE users
ADD COLUMN subscription_status ENUM('Free', 'Premium') DEFAULT 'Free',
    ADD COLUMN subscription_expiry DATE DEFAULT NULL;
ALTER TABLE events
MODIFY COLUMN e_image TEXT;
CREATE TABLE event_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
DROP TABLE IF EXISTS event_images;
ALTER TABLE journals
ADD COLUMN cover_image VARCHAR(255) DEFAULT NULL;
CREATE TABLE support_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_type ENUM('Help', 'Bug') NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    images TEXT,
    status ENUM('New', 'In Progress', 'Stalled', 'Resolved') DEFAULT 'New',
    owner_id INT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE replies (
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    user_id INT NOT NULL,
    reply_text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (request_id) REFERENCES support_requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

ALTER TABLE `journals`
ADD COLUMN `is_hidden` BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN `hidden_by` INT NULL,
ADD COLUMN `hidden_at` DATETIME NULL,
ADD CONSTRAINT `fk_hidden_by_user` FOREIGN KEY (`hidden_by`) REFERENCES `users`(`user_id`);

ALTER TABLE `users`
MODIFY `role` ENUM('traveller', 'editor', 'admin', 'support_tech') NOT NULL DEFAULT 'traveller';

CREATE TABLE yogo.ban_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(20) NOT NULL,      -- 'banned' or 'unbanned'
    reason VARCHAR(255),              -- nullable because unban might not have reason
    ban_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


