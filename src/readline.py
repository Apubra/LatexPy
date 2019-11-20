# Open the file with read only permit
f = open('/root/Code/Personal/Git Hub/LatexPy/doc/chapter1.tex', "r+")
# use readlines to read all lines in the file
# The variable "lines" is a list containing all lines in the file
# datas = f.read()
lines = f.readlines()
# close the file after reading the lines.
f.close()
# print(lines)
for line in lines:
    listx = list(line.split())
    print(listx)
    print(line.split())
    print(listx.index('This'))
    # for val in line.split():
    #     print(listx.index(val))
    break