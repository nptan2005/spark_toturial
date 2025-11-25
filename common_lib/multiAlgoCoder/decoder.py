from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from ..utilities.utils import Utils as utils


class decoder:

    def __init__(self, masterKey:bytes = None , key: bytes = None , iv: bytes = None  ):
        self.__master_key = masterKey
        self.__key = key
        self.__iv = iv
        self.__enKey = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__master_key = None
        self.__key = None
        self.__iv = None

    def __del__(self):
        del self.__master_key, self.__key, self.__iv 

    @property
    def AESEncryptKey(self):
        return self.__enKey
    
    @AESEncryptKey.setter
    def AESEncryptKey(self, value):
        self.__enKey = value

    @property
    def AESKey(self):
        """Clear Client Key"""
        return self.__key
    
    @AESKey.setter
    def AESKey(self, value):
        self.__key = value
    

    @property
    def AESMasterKey(self):
        return self.__master_key
    
    @AESMasterKey.setter
    def AESMasterKey(self, value):
        self.__master_key = value
    
    @property
    def AESIVMasterKey(self):
        return self.__iv
    
    @AESIVMasterKey.setter
    def AESIVMasterKey(self, value):
        self.__iv = value
    
    # cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()): Tạo một đối tượng giải mã Cipher với các tham số tương tự như hàm __encrypt.
    # decryptor = cipher.decryptor(): Tạo một đối tượng decryptor để thực hiện giải mã.
    # unpadder = PKCS7(algorithms.AES.block_size).unpadder(): Tạo một đối tượng unpadder để giải mã padding PKCS7.
    # decrypted_data = decryptor.update(encrypt_ciphertext) + decryptor.finalize(): Giải mã một phần dữ liệu đã được mã hóa.
    # return unpadder.update(decrypted_data) + unpadder.finalize(): Giải mã padding và trả về chuỗi đã giải mã.
    # unpadder.update(decrypted_data): Giải mã padding cho phần dữ liệu đã giải mã.
    # unpadder.finalize(): Hoàn thành quá trình giải mã padding và trả về chuỗi đã giải mã.

    def AESDecrypt(self, encrypt_ciphertext: bytes, key: bytes, iv:bytes) -> bytes:
        """Descryt value by AES."""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder = PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = decryptor.update(encrypt_ciphertext) + decryptor.finalize()
        return unpadder.update(decrypted_data) + unpadder.finalize()
    
    def AESDecyptDataToPlainText(self, encrypt_ciphertext: bytes, key: bytes, iv:bytes) -> str:
        return self.AESDecrypt(encrypt_ciphertext, key, iv).decode()

 
    # Giải mã key AES bằng master key
    def AESDecryptKey(self, key:bytes) -> bytes:
        """Decrypt client Key (AES) by master key"""
        self.__key = self.AESDecrypt(key, self.__master_key, self.__iv)
        return self.__key
    

    def AESDecryptDataByKey(self, enValue:bytes, key:bytes, iv:bytes) -> str:
        return self.AESDecrypt(enValue, key, iv)
    
    
    def AESDecryptData(self,enValue:bytes, iv:bytes) -> str:
        if self.__key is None:
            self.__key = self.AESDecryptKey(self.__enKey)


        if self.__key is not None:
            return self.AESDecyptDataToPlainText(enValue, self.__key, iv)
        
        return None
    
    
    
    def AESDecryptBase64Data(self,enValue:str, iv:str) -> str:
        bytesValue = utils.convertBase64ToBytes(enValue)
        bytesIV =  utils.convertBase64ToBytes(iv)
        return self.AESDecryptData(bytesValue, bytesIV)
    
    

    def AESDecryptDataFromFile(self,valuePath:str, ivPath:str) -> str:
        if utils.checkFileIsExist(valuePath) == False or utils.checkFileIsExist(valuePath) == False:
            return None
        
        _encrypt_data = utils.readFile(valuePath, "rb")

        _iv_data = utils.readFile(ivPath, "rb")

        return self.AESDecryptData(_encrypt_data, _iv_data)
        


    
    

    

