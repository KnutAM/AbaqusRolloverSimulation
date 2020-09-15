class IncompatibleWheelError(Exception)
    """Exception raised when a wheel not compatible with the requested loading is used

    Attributes:
        in -- input salary which caused the error
        message -- explanation of the error
    """
	
	def __init__(self, rolling_angle, contact_angle):
		self.rolling_angle = rolling_angle
		self.contact_angle = contact_angle
		super().__init__(self.message)