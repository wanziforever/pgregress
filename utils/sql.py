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
    for i in range(len(sqlstr)):
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
        if c == '$' and sqlstr[i+1] == '$':
            # in a double $$ sign
            indollar = not indollar
            i += 1
            continue

        if c == ';' and inquora is False and indollar is False:
            newstr = sqlstr[startpos:i].strip()
            # remove newlines
            sqls.append(newstr)
            startpos = i+1

    if i > startpos:
        sqls.append(sqlstr[startpos:i].strip())
    return sqls
