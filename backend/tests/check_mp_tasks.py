
import mediapipe as mp
try:
    print(dir(mp.tasks))
    from mediapipe.tasks.python import vision
    print(dir(vision))
except Exception as e:
    print(e)
