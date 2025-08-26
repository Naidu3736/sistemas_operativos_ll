class Process:
    def __init__(self, PID = -1, size = 0):
        """
        Inicializa el proceso

        Args:
            PID (int): Identificador del proceso
            size (int): Tamaño del proceso
        """
        self.size = size
        self.PID = PID