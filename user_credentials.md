# MD Wallet - User Credentials

This document contains the login credentials for all users of the MD Wallet application. Please share the appropriate credentials with each user.

## Login Information

The application is accessible at:
- Local URL: http://localhost:8501 (when running locally)
- Streamlit Cloud URL: [Your Streamlit Cloud URL when deployed]

## User Credentials

| Username | Password           | Email                    |
|----------|-------------------|--------------------------|
| admin    | admin123          | admin@mdwallet.com       |
| usuario1 | user123           | user1@mdwallet.com       |
| Valeríya | Bw7$pQzX9tLm      | valeríya@mdwallet.com    |
| Luis     | K3r@NvD8sYfE      | luis@mdwallet.com        |
| Joao     | P9j$Tz5LqWxH      | joao@mdwallet.com        |
| Humberto | G4h&FmV7cRpZ      | humberto@mdwallet.com    |
| Goncalo  | X2s#Jb6QnDvA      | goncalo@mdwallet.com     |
| Josue    | M5t@Rz8PkLdS      | josue@mdwallet.com       |
| Bruno    | C7f$Qp3HjNxY      | bruno@mdwallet.com       |
| PauloP   | V9g&Zk4TmBwJ      | paulop@mdwallet.com      |
| PauloR   | L6h#Xd2RqFsP      | paulor@mdwallet.com      |
| Jose     | T8j$Mn5VcKpZ      | jose@mdwallet.com        |
| Ricardo  | D3k@Qb7GxWfS      | ricardo@mdwallet.com     |
| Antonio  | N4m&Vp9JzTcR      | antonio@mdwallet.com     |
| Sodia    | F6s#Hd3LqBxZ      | sodia@mdwallet.com       |
| Timoteo  | R9t$Kp5MnVjW      | timoteo@mdwallet.com     |
| Armando  | H2v@Zf8QcPdG      | armando@mdwallet.com     |
| Nelson   | W7g&Jm4TzBsX      | nelson@mdwallet.com      |
| Tudor    | S3k#Vb9NpRfD      | tudor@mdwallet.com       |
| Mika     | Y5m$Qz7HjLcT      | mika@mdwallet.com        |
| Lucas    | B8p@Xd4GvWkS      | lucas@mdwallet.com       |
| Carla    | J6r&Zn2TmFqP      | carla@mdwallet.com       |

## Important Notes

1. **Long-Term Login**: The application is configured to keep users logged in for 365 days on the same device. Users won't need to log in again unless they clear their browser cookies or use a different device.

2. **Data Persistence**: All user data (transactions, history, settings) is stored in MongoDB and will be available whenever they log in, even from different devices.

3. **Password Security**: Passwords are stored securely using bcrypt hashing. If a user forgets their password, an administrator will need to reset it.

4. **User Data Separation**: Each user's data is completely separate from other users. Users can only see and modify their own data.

## For Administrators

If you need to add more users or reset passwords, you can:

1. Use the `utils/generate_hash.py` utility to generate bcrypt hashes for new passwords
2. Update the `data/config.yaml` file with the new user information
3. Restart the application for changes to take effect

For any issues or support, please contact the system administrator. 