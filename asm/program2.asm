LOAD  F2, 0(R1)      # I1: load R1 from memory
MUL   F6, F2, F4     # I2: RAW on R1 (waits for I1)
ADD   F2, F6, F4     # I3: RAW on R3 (waits for I2)
MUL   F2, F1, F3     # I4: independent, may execute out-of-order
ADD   R1, R1, R1    # I5: RAW on R7 (waits for I4) and R1 (waits for I1)
STORE F2, 0(R1)     # I6: RAW on R10 (waits for I5)
