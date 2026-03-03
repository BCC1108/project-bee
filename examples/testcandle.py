lst = []
print(lst is None)      # 输出: False
print(lst == None)      # 输出: False（虽然不推荐用 == 比较 None）
print(lst == [])        # 输出: True
print(len(lst) == 0)    # 输出: True