import sys; sys.path.insert(0, ".")
import data
s = data.prices("^SOX", "1999-01-01")
for i in range(1, len(s)):
    r = (s[i][1] / s[i-1][1] - 1) * 100
    if r <= -9: print(s[i][0], round(r, 2))
print("last", s[-1])
