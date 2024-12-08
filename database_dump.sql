-- MySQL dump 10.13  Distrib 9.1.0, for Win64 (x86_64)
--
-- Host: localhost    Database: system_db
-- ------------------------------------------------------
-- Server version	9.1.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `balance_history`
--

DROP TABLE IF EXISTS `balance_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `balance_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `type` enum('deposit','withdrawal') NOT NULL,
  `created_at` timestamp DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `balance_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `balance_history`
--

LOCK TABLES `balance_history` WRITE;
/*!40000 ALTER TABLE `balance_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `balance_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `banking_requests`
--

DROP TABLE IF EXISTS `banking_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `banking_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `request_type` enum('deposit','withdrawal') NOT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `reason` text,
  `created_at` timestamp DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `banking_requests_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `banking_requests`
--

LOCK TABLES `banking_requests` WRITE;
/*!40000 ALTER TABLE `banking_requests` DISABLE KEYS */;
INSERT INTO `banking_requests` VALUES (1,15,100.00,'deposit','pending',NULL,'2024-12-07 20:32:35'),(2,15,500.00,'deposit','pending',NULL,'2024-12-07 20:33:49'),(3,9,500.00,'deposit','pending',NULL,'2024-12-07 20:38:39'),(4,20,50.00,'deposit','pending',NULL,'2024-12-07 21:49:21'),(5,26,500.00,'deposit','pending',NULL,'2024-12-07 23:38:52');
/*!40000 ALTER TABLE `banking_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_activity`
--

DROP TABLE IF EXISTS `user_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_activity` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `activity_type` varchar(255) NOT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `created_at` datetime DEFAULT 0,
  `username` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `user_activity_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_activity`
--

LOCK TABLES `user_activity` WRITE;
/*!40000 ALTER TABLE `user_activity` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_activity` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(191) NOT NULL,
  `password` varchar(191) NOT NULL,
  `is_admin` tinyint(1) DEFAULT '0',
  `is_master_agent` tinyint(1) DEFAULT '0',
  `is_super_agent` tinyint(1) DEFAULT '0',
  `is_user_agent` tinyint(1) DEFAULT '1',
  `is_blocked` tinyint(1) DEFAULT '0',
  `referred_by` int DEFAULT NULL,
  `referral_code` varchar(191) DEFAULT NULL,
  `commission_percentage` float DEFAULT '0',
  `is_deposit_enabled` tinyint(1) DEFAULT '1',
  `is_withdraw_enabled` tinyint(1) DEFAULT '1',
  `balance` decimal(10,2) DEFAULT '0.00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `referral_code` (`referral_code`),
  KEY `fk_referred_by` (`referred_by`),
  CONSTRAINT `fk_referred_by` FOREIGN KEY (`referred_by`) REFERENCES `users` (`id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`referred_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (9,'admin','$2b$12$f/RLqT1yrdnTX6qpAJuuVufOHGCZDDPqC8/0cKVU/mb8xFxOfpvSC',1,0,0,1,0,NULL,'ADMIN123',0,1,1,0.00),(15,'watch','$2b$12$r53ZGbzhgD9XXqZbkpj9v.yGcWND1Pfso0Gs5SM94AxptjkJQN6VW',0,0,0,1,0,NULL,'watch',0,1,1,0.00),(20,'Shemu','$2b$12$CxCzmf/LABxmMTGIaIQA8emYvFiuOxNfHA3jcocwJ343tLNgGb/26',0,0,0,1,0,NULL,'Shemu',0,1,1,0.00),(21,'Master','$2b$12$9mDoWFV59DieIuzr.XqxoeNm6h/djXkn9HqqIv9dYZQfnnH9x78Oe',0,0,1,0,0,NULL,NULL,10,1,1,0.00),(22,'Super','$2b$12$l2sXp7RLGjyN2vxPZZqwHODNNbTaPqTjI8bAYLXcd2Jqu7ngNSmE6',0,1,0,0,0,NULL,NULL,10,1,1,0.00),(23,'Karim','$2b$12$ZdmxngIeK/DwjZfJ.AfMYu4nnekG/S8fmHbO72FD0UvuUWuNTm2Gm',0,0,1,1,0,22,'22fc8338',10,1,1,0.00),(25,'simu','$2b$12$7cciC9mmCQdtXvBvaDPW9.yZZT/6O0Ja3cO5fo/.Y8CjvXDd2gzY.',0,0,1,0,0,NULL,NULL,10,1,1,0.00),(26,'rachi','$2b$12$rdqgWKBv6vZlRZ11Nkig0uAhSeYj0bIzlyphZ1omsGuKD23YhTye2',0,0,0,1,0,25,'43808409',50,1,1,0.00),(27,'sowad','$2b$12$NYfV0yy7GXFl6wjKee/wr.cJETDOzf.2zwRvCwRyJDiDXJO00gmfi',0,0,0,1,0,NULL,NULL,10,1,1,0.00),(28,'pagla','$2b$12$9kfwSuyJeTkYexMgZpnFYeXcWuKzC45ICIw1qpwUbbdZgMLHuUQVa',0,0,0,1,0,NULL,'e8c226072ed878cf',0,1,1,0.00);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-12-08 16:18:46
