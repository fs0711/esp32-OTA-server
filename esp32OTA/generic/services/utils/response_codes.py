# RESPONSE CODES

CODE_SUCCESS = 200
CODE_DEPRECATED_API = 299

CODE_HTTP_401 = 401
CODE_HTTP_452 = 452
CODE_UNAUTHENTICATED_ACCESS = 401
CODE_UNAUTHORIZED_ACCESS = 403


# OPERATION FAILED CODES
CODE_CREATE_FAILED = 1001
CODE_READ_FAILED = 1002
CODE_UPDATE_FAILED = 1003
CODE_DELETE_FAILED = 1004

# INACTIVE CASES
CODE_USER_IS_INACTIVE = 2000

# INVALID PARAMS OR INVALID CALL
CODE_MISSING_PARAMETERS = 4000
CODE_INVALID_CALL = 4001
CODE_WRONG_PARAMETERS = 4002
CODE_VALIDATION_FAILED = 4003
CODE_PLATFORM_INCORRECT = 4004

# TOKEN STATUS CODES - 5000
CODE_TOKEN_EXPIRED = 5001
CODE_TOKEN_INVALID = 5002
CODE_TOKEN_REVOKED = 5003
CODE_INVALID_OTP = 5004

# NOT FOUND CODES - 6000
CODE_RECORD_NOT_FOUND = 6000
CODE_USER_NOT_FOUND = 6003

# INVALID CODES - 7000
CODE_INVALID_EMAIL_ADDRESS = 7001
CODE_INVALID_EMAIL_ADDRESS_OR_PASSWORD = 7002
CODE_INVALID_PHONE_NUMBER = 7003
CODE_INVALID_USER_TYPE = 7004
CODE_INVALID_USER_ID = 7005
CODE_INVALID_PASSWORD = 7006
CODE_INVALID_DATE_FORMAT = 7007

# Extra Params Given - 8000
CODE_EXTRA_PARAMS_GIVEN = 8000

# ALREADY EXIST CODES - 9000
CODE_EMAIL_ADDRESS_ALREADY_EXISTS = 9001
CODE_PHONE_NUMBER_ALREADY_EXISTS = 9002
CODE_USER_ALREADY_EXIST = 9003
CODE_DOCTOR_ID_ALREADY_EXISTS = 9004
CODE_DEPARTMENT_ID_ALREADY_EXISTS = 9005
CODE_DEPARTMENT_NAME_ALREADY_EXISTS = 9006

# LEADS CODES - 10000
CODE_LEAD_OUT_OF_BOUND = 10000

# Response Messages
MESSAGE_SUCCESS = "Successful response"
MESSAGE_OPERATION_FAILED = "Operation Failed"
MESSAGE_DEPRECATED_API = "API deprecated"
MESSAGE_VALIDATION_FAILED = "Validation Failed."
MESSAGE_INCORRECT_PASSWORD = "Incorrect Password."
MESSAGE_LOGIN_SUCCESS = "Successfully logged in User"
MESSAGE_LOGOUT_SUCCESS = "Successfully logged out User"
MESSAGE_INVALID_DATA = "{} is incorrect"
MESSAGE_NOT_FOUND_DATA = "{} with this {} was not found"
MESSAGE_ALREADY_EXISTS_DATA = "{} with this {} already Exists"
MESSAGE_IMMUTABLE_DATA_RECEIVED = "The Fields {} cannot be Updated"
MESSAGE_PLATFORM_INCORRECT = \
    "Platform Url Parameter Incorrect. Only {} are allowed"
MESSAGE_PASSWORD_RESET_EMAIL_SENT =\
    "Password reset email has been successfully sent."
MESSAGE_PASSWORD_CHANGED_SUCCESSFULLY =\
    "Password has been successfully changed."
MESSAGE_MANAGER_NOT_ALLOWED =\
    "The Manager '{}' is not Allowed for Role '{}'"
MESSAGE_NOT_ALLOWED =\
    "The {} '{}' is not Allowed for {} '{}'"
MESSAGE_MPO_CANNOT_DO_ON_BEHALF_OF =\
    "The Role MPO cannot set On Behalf of other than self"
MESSAGE_NOT = "{} is not {}, Cannot perform this task."
MESSAGE_NOT_SELF = "{} has to be the {} to perform this task."
MESSAGE_NOT_CHILD =\
    "The {} '{}' is not Child of {} '{}'"
MESSGAE_PARAM_NOT_ALLOWED_AT_ONCE = "The Paramater's {} cannot be entered at once"
MESSAGE_MISSING_PARAMETERS = "Some parameters are missing {}"
MESSAGE_EXTRA_PARAMETERS = "Extra Not Needed Parameter Given '{}' "
MESSAGE_NON_ADMIN_PROMPT = "Only Admin can perform this Task"
MESSAGE_CANNOT_ASSIGN = "{} can only be assigned to {}"
MESSAGE_TARGET_OVERFLOW = "The total assigned Target->{} which is {} can not be greater than Manager Target->{} which\
    is {}"
MESSAGE_OUT_OF_STOCK = "The Product '{}' is out of stock the current quantity of product is '{}'"
MESSAGE_PARAM_FORMAT_INCORRECT = "The Field {} should be in format {}"
MESSAGE_CANNOT_SUSPEND_HAS_CHILD = "{} Suspend Failed, Record has Children first suspend them."
MESSAGE_LOCATION_NOT_IN_ASSIGNED = "The Location '{}' is not assigned to '{}' "
MESSAGE_HAS_TO_BE_LESS_THAN = "{} has to be less than {}"
# MESSAGE_ID_PARAMETER_MISSING = "Id parameter is missing"
# MESSAGE_INVALID_CALL = "Invalid call"
# MESSAGE_RELATIVE_MISSING_PARAMETERS = "Some Relative parameters are missing"
# MESSAGE_ADDRESS_MISSING_PARAMETERS = "Some Address parameters are missing"
# MESSAGE_DICTIONARY_MISSING_PARAMETERS = "Some {} parameters are missing"
MESSAGE_AUTHENTICATION_FAILED =\
    "Authentication failed. Invalid or Expired token."
MESSAGE_UNAUTHENTICATED_ACCESS = "Unauthenticated access."
MESSAGE_UNAUTHORIZED_ACCESS = "Unauthorized access."
MESSAGE_USER_IS_INACTIVE = "User is Inactive"
# MESSAGE_PHONE_ALREADY_VERIFIED = "Phone Number is already verified"
# MESSAGE_EMAIL_ALREADY_VERIFIED = "Email Address is already verified"
# MESSAGE_VERIFY_EMAIL_ADDRESS_FIRST = "Please verify email address first."
# MESSAGE_PASSWORDS_DO_NOT_MATCH = "Passwords do not match"

# MESSAGE_INVALID_EMAIL_ADDRESS = "Invalid email address"
# MESSAGE_INVALID_PHONE_NUMBER = "Invalid Phone Number"
# MESSAGE_INVALID_EMAIL_ADDRESS_OR_PASSWORD = "Invalid email address/password"
MESSAGE_INVALID_LEAD = "This lead is not from your team"
MESSAGE_INVALID_OTP = "Invalid OTP"
MESSAGE_INVALID_TOKEN = "Invalid Token"
MESSAGE_TOKEN_EXPIRED = "Token has Expired"
MESSAGE_TOKEN_REVOKED = "Token has been Revoked"
MESSAGE_INVALID_PHONENUMBER = "No lead found for this number"
MESSAGE_DUPLICATE_ENTRY = "Record Already Exists"


# GENERAL ERRORS
MESSAGE_SYSTEM_ERROR = 'Server is not responding at the moment.'
MESSAGE_GENERAL_ERROR = "Something went wrong. Please try again."
MESSAGE_MISSING_OR_INVALID_SESSION_KEY = "Missing or invalid session key."

# USER
MESSAGE_USER_VERIFIED = "User verified."
MESSAGE_USER_EMAIL_VERIFIED = "User email address verified."
MESSAGE_USER_PHONE_VERIFIED = "User phone number verified."

# TWILIO
MESSAGE_TWILIO_INVALID_NUMBER = "Twilio Exception"
