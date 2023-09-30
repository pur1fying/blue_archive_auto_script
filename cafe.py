name_st = "爱丽丝爱丽丝(邀请小春"
student_name = ["爱丽丝(", "爱丽丝", "小春"]
detected_name = []
i = 0
while i < len(name_st):
    for j in range(0,len(student_name)):
         if name_st[i] == student_name[j][0]:
            flag = True
            for k in range(1,len(student_name[j])):
                if name_st[i+k] != student_name[j][k]:
                     flag = False
                     break
            if flag:
                detected_name.append(student_name[j])
                i = i + len(student_name[j]) - 1
                break
    i = i + 1
print(detected_name)