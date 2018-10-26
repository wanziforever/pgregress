def parse_sqls(sqlstr):
    """
    :type sqlstr: str
    :param sqlstr: a complex sql clause

    :rtype: list of string
    :returns: a list of sub sqls
    """
    #sqlstr = sqlstr.strip()
    #if sqlstr[0] == '{':
    #    # remove the left and right {}
    #    sqlstr = sqlstr[1:-1]
        
    sqlstr = sqlstr.strip()

    sqls = []
    startpos = 0
    newstr = ''
    inquora = False
    indollar = False
    length = len(sqlstr)
    i = -1
    trigger_name = ""
    while i < length-1:
        i += 1
        c = sqlstr[i]
        if c == '\'' and inquora is False:
            # handle wrap quora case
            if i > 0 and sqlstr[i-1] == '\\':
                pass
            else:
                inquora = True
            continue

        if c == '\'' and inquora is True:
            if i > 0 and sqlstr[i-1] == '\\':
                pass
            else:
                inquora = False
            continue

        # for simple implemetation, ignore the wrap \$$ case handling
        if c == '$':
            tmp = []
            while True:
                i += 1
                if sqlstr[i] == "$":
                    break
                if i > 10000:
                    print("strange !! invalid trigger ")
                    exit(1)
                tmp.append(sqlstr[i])
            trigger_name = "".join(tmp)
            #if not indollar:
            #    print("find a new trigger", trigger_name)
            #else:
            #    print("end trigger", trigger_name)
            indollar = not indollar
            continue

        if c == ';' and inquora is False and indollar is False:
            newstr = sqlstr[startpos:i+1].strip()
            # remove newlines
            sqls.append(newstr)
            startpos = i+1

    if i > startpos:
        sqls.append(sqlstr[startpos:].strip())

    #for index, sql in enumerate(sqls):
    #    print("%s -- %s" % (index, sql))

    return sqls
