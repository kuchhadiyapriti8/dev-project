-- Insert 20 members, 5 moderators, and 2 administrators
INSERT INTO users (username, password_hash, email, first_name, last_name, birth_date, location, profile_image, role, status) VALUES
('member1', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member1@example.com', 'John', 'Doe', '1990-01-01', 'New York', 'profile1.jpg', 'member', 'active'),
('member2', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member2@example.com', 'Jane', 'Doe', '1989-02-02', 'Los Angeles', 'profile2.jpg', 'member', 'active'),
('member3', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member3@example.com', 'Alice', 'Smith', '1991-03-03', 'Chicago', 'profile3.jpg', 'member', 'active'),
('member4', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member4@example.com', 'Bob', 'Johnson', '1992-04-04', 'Houston', 'profile4.jpg', 'member', 'active'),
('member5', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member5@example.com', 'Charlie', 'Williams', '1993-05-05', 'San Francisco', 'profile5.jpg', 'member', 'active'),
('member6', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member6@example.com', 'Diana', 'Brown', '1994-06-06', 'Philadelphia', 'profile6.jpg', 'member', 'active'),
('member7', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member7@example.com', 'Ethan', 'Jones', '1995-07-07', 'San Diego', 'profile7.jpg', 'member', 'active'),
('member8', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member8@example.com', 'Fiona', 'Garcia', '1996-08-08', 'Dallas', 'profile8.jpg', 'member', 'active'),
('member9', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member9@example.com', 'George', 'Martinez', '1997-09-09', 'San Jose', 'profile9.jpg', 'member', 'active'),
('member10', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member10@example.com', 'Hannah', 'Hernandez', '1998-10-10', 'Austin', 'profile10.jpg', 'member', 'active'),
('member11', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member11@example.com', 'Ian', 'Wilson', '1999-11-11', 'Columbus', 'profile11.jpg', 'member', 'active'),
('member12', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member12@example.com', 'Julia', 'Anderson', '1988-12-12', 'Indianapolis', 'profile12.jpg', 'member', 'active'),
('member13', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member13@example.com', 'Kevin', 'Thomas', '1990-01-13', 'Jacksonville', 'profile13.jpg', 'member', 'active'),
('member14', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member14@example.com', 'Laura', 'White', '1991-02-14', 'San Francisco', 'profile14.jpg', 'member', 'active'),
('member15', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member15@example.com', 'Mia', 'Jackson', '1992-03-15', 'Seattle', 'profile15.jpg', 'member', 'active'),
('member16', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member16@example.com', 'Noah', 'Martin', '1993-04-16', 'Denver', 'profile16.jpg', 'member', 'active'),
('member17', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member17@example.com', 'Olivia', 'Thompson', '1994-05-17', 'Boston', 'profile17.jpg', 'member', 'active'),
('member18', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member18@example.com', 'Paul', 'Lee', '1995-06-18', 'Detroit', 'profile18.jpg', 'member', 'active'),
('member19', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member19@example.com', 'Quinn', 'Perez', '1996-07-19', 'Nashville', 'profile19.jpg', 'member', 'active'),
('member20', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'member20@example.com', 'Riley', 'Scott', '1997-08-20', 'Baltimore', 'profile20.jpg', 'member', 'active'),
('moderator1', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'moderator1@example.com', 'Alice', 'Smith', '1985-05-05', 'Chicago', 'profile21.jpg', 'moderator', 'active'),
('moderator2', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'moderator2@example.com', 'Bob', 'Johnson', '1986-06-06', 'Houston', 'profile22.jpg', 'moderator', 'active'),
('moderator3', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'moderator3@example.com', 'Charlie', 'Williams', '1987-07-07', 'San Francisco', 'profile23.jpg', 'moderator', 'active'),
('moderator4', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'moderator4@example.com', 'David', 'Brown', '1988-08-08', 'Philadelphia', 'profile24.jpg', 'moderator', 'active'),
('moderator5', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'moderator5@example.com', 'Eve', 'Jones', '1989-09-09', 'Dallas', 'profile25.jpg', 'moderator', 'active'),
('admin1', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'admin1@example.com', 'Sarah', 'Williams', '1980-03-03', 'San Francisco', 'profile26.jpg', 'admin', 'active'),
('admin2', '5e884898da28047151d0e56f8dc6292773603d0d2b1e9b60e2e7f71e3c3e3e1a', 'admin2@example.com', 'Robert', 'Brown', '1975-12-15', 'Boston', 'profile27.jpg', 'admin', 'active');


-- Insert 20 messages
INSERT INTO messages (user_id, title, content) VALUES
(1, 'Welcome to the Community!', 'Hello everyone! We are excited to have you here. Introduce yourself and let us know what you’re interested in.'),
(2, 'Feature Request', 'I would love to see a new feature that allows us to filter posts by tags. What do you think?'),
(3, 'Community Guidelines', 'Please make sure to follow the community guidelines to keep our space welcoming for everyone.'),
(4, 'Bug Report', 'I found a bug in the latest update. The search function is not working as expected.'),
(5, 'Event Announcement', 'We are hosting a community event next week. Join us for some fun activities!'),
(6, 'Help Needed', 'Can someone help me with an issue I’m having with my profile settings?'),
(7, 'General Discussion', 'What do you think about the new feature that was recently added?'),
(8, 'Introduction', 'Hi, I’m new here! I’m looking forward to connecting with everyone.'),
(9, 'Suggestion Box', 'If you have any suggestions for improving the site, please let us know.'),
(10, 'Feedback Request', 'We would love to hear your feedback on our latest updates.'),
(11, 'Thank You', 'A big thank you to everyone who participated in our recent survey!'),
(12, 'Resource Sharing', 'Here’s a useful resource that I think everyone will benefit from.'),
(13, 'FAQ', 'We’ve updated our FAQ section. Check it out for answers to common questions.'),
(14, 'Reminder', 'Don’t forget to participate in our ongoing discussion about future improvements.'),
(15, 'Poll', 'Please take a moment to vote in our poll about new features.'),
(16, 'Guidance', 'Looking for some guidance on how to use the advanced settings feature.'),
(17, 'Update', 'We have a new update rolling out tomorrow. Stay tuned for details.'),
(18, 'Congratulations', 'Congratulations to our member of the month!'),
(19, 'Survey Results', 'The results of our recent survey are now available.'),
(20, 'Community Milestone', 'We’ve reached a new milestone! Thank you for being part of our community.');


-- Insert 10 replies
INSERT INTO replies (message_id, user_id, content) VALUES
(1, 2, 'Thanks for the warm welcome! I’m excited to be here.'),
(1, 3, 'Looking forward to getting involved.'),
(2, 1, 'Filtering by tags is a great idea! I would find that very useful.'),
(2, 4, 'Yes, a tagging system would definitely help with organization.'),
(3, 5, 'I’ll make sure to review the guidelines.'),
(4, 6, 'I’ve noticed the same issue. Hope it gets fixed soon.'),
(5, 7, 'Can’t wait for the event! Looking forward to it.'),
(6, 8, 'I’ll help you with that. What’s the issue with your profile settings?'),
(7, 9, 'The new feature is fantastic! Really enhances the user experience.'),
(8, 10, 'Welcome to the community! Glad to have you here.');
