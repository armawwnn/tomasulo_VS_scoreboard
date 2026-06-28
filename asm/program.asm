LOAD  R1, 0(R2)      # I1: load R1 from memory
MUL   R3, R1, R4     # I2: RAW on R1 (waits for I1)
ADD   R5, R3, R6     # I3: RAW on R3 (waits for I2)
SUB   R7, R8, R9     # I4: independent, may execute out-of-order
ADD   R10, R7, R1    # I5: RAW on R7 (waits for I4) and R1 (waits for I1)
STORE R10, 4(R2)     # I6: RAW on R10 (waits for I5)
