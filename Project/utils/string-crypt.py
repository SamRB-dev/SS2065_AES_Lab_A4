# XOR Encryption and Decryption
# Function definition can be obfuscated for making it anti reverse engineering and less obvious 
encrypt = "test"
str = ""
for i in encrypt:
    str += chr(ord(i) ^ 1)
print(f"Plain Text: {encrypt}")
print(f"Encrypted: {str}")

result = ""
for i in str:
    result += chr(ord(i) ^ 1)
print(f"Decrypted: {result}")  