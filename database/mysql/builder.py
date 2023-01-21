
import re


class DatabaseException(Exception):
    pass

class DataException(Exception):
    pass

class InvalidArgumentException(Exception):
    pass


class BaseBuilder:

    """
     * Reset DELETE data flag
     *
     * @var bool
    """
    resetDeleteData = False

    """
     * QB SELECT data
     *
     * @var array
    """
    QBSelect = []

    """
     * QB DISTINCT flag
     *
     * @var bool
    """
    QBDistinct = False

    """
     * QB FROM data
     *
     * @var array
    """
    QBFrom = []

    """
     * QB JOIN data
     *
     * @var array
    """
    QBJoin = []

    """
     * QB WHERE data
     *
     * @var array
    """
    QBWhere = []

    """
     * QB GROUP BY data
     *
     * @var array
    """

    QBGroupBy = []

    """
     * QB HAVING data
     *
     * @var array
    """
    QBHaving = []

    """
     * QB keys
     *
     * @var array
    """
    QBKeys = []

    """
     * QB LIMIT data
     *
     * @var bool|int
    """
    QBLimit = False

    """
     * QB OFFSET data
     *
     * @var bool|int
    """
    QBOffset = False

    """
     * QB ORDER BY data
     *
     * @var array|string|None
    """
    QBOrderBy = []

    """
     * QB NO ESCAPE data
     *
     * @var array
    """
    QBNoEscape = []

    """
     * QB data sets
     *
     * @var array
    """
    QBSet = []

    """
     * QB WHERE group started flag
     *
     * @var bool
    """
    QBWhereGroupStarted = False

    """
     * QB WHERE group len
     *
     * @var int
    """
    QBWhereGroupCount = 0

    """
     * Ignore data that cause certain
     * exceptions, for example in case of
     * duplicate keys.
     *
     * @var bool
    """
    QBIgnore = False

    """
     * A reference to the database connection.
     *
     * @var BaseConnection
    """
    db = None

    """
     * Name of the primary table for self instance.
     * Tracked separately because QBFrom gets escaped
     * and prefixed.
     *
     * @var string
    """
    tableName = None

    """
     * ORDER BY random keyword
     *
     * @var array
    """
    randomKeyword = [
        'RAND()',
        'RAND(%d)',
    ]

    """
     * COUNT string
     *
     * @used-by CI_DB_driver::count_all()
     * @used-by BaseBuilder::count_all_results()
     *
     * @var string
    """
    len= 'SELECT COUNT(*) AS '

    """
     * Collects the named parameters and
     * their values for later binding
     * in the Query object.
     *
     * @var array
    """
    binds = []

    """
     * Collects the key len for named parameters
     * in the Query object.
     *
     * @var array
    """
    bindsKeyCount = []

    """
     * Some databases, like SQLite, do not by default
self,      * allow limiting of delete clauses.
     *
     * @var bool
    """
    canLimitDeletes = True

    """
     * Some databases do not by default
self,      * allow limit update queries with WHERE.
     *
     * @var bool
    """
    canLimitWhereUpdates = True

    """
     * Specifies which sql statements
     * support the ignore option.
     *
     * @var array
    """
    supportedIgnoreStatements = []

    """
     * Builder testing mode status.
     *
     * @var bool
    """
    testMode = False

    """
     * Tables relation types
     *
     * @var array
    """
    joinTypes = [
        'LEFT',
        'RIGHT',
        'OUTER',
        'INNER',
        'LEFT OUTER',
        'RIGHT OUTER',
    ]

    """
     * Strings that determine if a represents a literal value or a field name
     *
     * @var string[]
    """
    isLiteralStr = []

    """
     * RegExp used to get operators
     *
     * @var string[]
    """
    pregOperators = []

    """
     * Constructor
     *
     * @param array|tableName
     *
     * @raises DatabaseException
    """
    def __init__(self, tableName, db, options=None):
        if (not tableName):
            raise DatabaseException('A table must be specified when creating a new Query Builder.')

        """
         * @var BaseConnection db
        """
        self.db = db

        self.tableName = tableName
        self.from_(tableName)

        if not options:
            for key in options:
                if hasattr(self, key):
                    setattr(self, key, options[key])

    """
     * Sets a test mode status.
     *
     * @return self
    """
    def testMode(self, mode = True):
        self.testMode = mode
        return self

    """
     * Ignore
     *
     * Set ignore Flag for next insert,
     * update or delete query.
     *
     * @return self
    """
    def ignore(self, ignore = True):
        self.QBIgnore = ignore
        return self
    

    """
     * Generates the SELECT portion of the query
     *
     * @param array|select
     *
     * @return self
    """
    def select(self, select = '*', escape = None):
        if isinstance(select, str):
            select = select.split(',')

        # If the escape value was not set, we will base it on the global setting
        if (not isinstance(escape, bool)):
            escape = self.db.protectIdentifiers

        for val in select:
            val = val.strip()

            if (val != ''):
                self.QBSelect = [val]

                """
                 * When doing 'SELECT null as field_alias FROM table'
                 * null gets taken as a field, and therefore escaped
                 * with backticks.
                 * self prevents null being escaped
                 * @see https://github.com/codeigniter4/CodeIgniter4/issues/1169
                """
                if val.strip().rfind('null') == 0:
                    escape = False

                self.QBNoEscape = [escape]

        return self

    """
     * Generates a SELECT MAX(field) portion of a query
     *
     * @return self
    """
    def selectMax(self, select = '', alias = ''):
        return self.maxMinAvgSum(select, alias)
    

    """
     * Generates a SELECT MIN(field) portion of a query
     *
     * @return self
    """
    def selectMin(self, select = '', alias = ''):
        return self.maxMinAvgSum(select, alias, 'MIN')
    

    """
     * Generates a SELECT AVG(field) portion of a query
     *
     * @return self
    """
    def selectAvg(self, select = '', alias = ''):
        return self.maxMinAvgSum(select, alias, 'AVG')
    

    """
     * Generates a SELECT SUM(field) portion of a query
     *
     * @return self
    """
    def selectSum(self, select = '', alias = ''):
        return self.maxMinAvgSum(select, alias, 'SUM')
    

    """
     * Generates a SELECT COUNT(field) portion of a query
     *
     * @return self
    """
    def selectCount(self, select = '', alias = ''):
        return self.maxMinAvgSum(select, alias, 'COUNT')
    

    """
     * SELECT [MAX|MIN|AVG|SUM|COUNT]()
     *
     * @used-by selectMax()
     * @used-by selectMin()
     * @used-by selectAvg()
     * @used-by selectSum()
     *
     * @raises DatabaseException
     * @raises DataException
     *
     * @return self
    """
    def maxMinAvgSum(self, select = '', alias = '', type = 'MAX'):
        if (select == ''):
            raise DataException("fornot InputGiven('Select')")

        if (select.find(',') != -1):
            raise DataException("forInvalidArgument('column name not separated by comma')")

        type = type.upper()

        if (not type in ['MAX', 'MIN', 'AVG', 'SUM', 'COUNT']):
            raise DatabaseException('Invalid function type: ' + type)

        if (alias == ''):
            alias = self.createAliasFromTable(select.strip())

        sql = type + '(' + self.db.protectIdentifiers(select.strip()) + ') AS ' + self.db.escapeIdentifiers(alias.strip())

        self.QBSelect  = [sql]
        self.QBNoEscape = [None]

        return self
    

    """
     * Determines the alias name based on the table
    """
    def createAliasFromTable(self, item):
        if (item.find('.') != -1):
            item = item.split('.')

            return item[-1]
        

        return item
    

    """
     * Sets a flag which tells the query compiler to add DISTINCT
     *
     * @return self
    """
    def distinct(self, val = True):
        self.QBDistinct = val

        return self
    

    """
     * Generates the FROM portion of the query
     *
     * @param array|from
     *
     * @return self
    """
    def from_(self, from_, overwrite = False):
        if (overwrite == True):
            self.QBFrom = []
            self.db.setAliasedTables([])
        

        for val in from_:
            if (val.find(',') != False):
                for v in val.split(','):
                    v = v.strip()
                    self.trackAliases(v)

                    self.QBFrom = [self.db.protectIdentifiers(v, True, None, False)]
        else:
                val = val.strip()

                # Extract any aliases that might exist. We use self information
                # in the protectIdentifiers to know whether to add a table prefix
                self.trackAliases(val)

                self.QBFrom = [self.db.protectIdentifiers(val, True, None, False)]
            
        

        return self
    

    """
     * Generates the JOIN portion of the query
     *
     * @return self
    """
    def join(self, table, cond, type = '', escape = None):
        if (type != ''):
            type = type.strip().upper()

            if (not type in self.joinTypes):
                type = ''
            else:
                type += ' '

        # Extract any aliases that might exist. We use self information
        # in the protectIdentifiers to know whether to add a table prefix
        self.trackAliases(table)

        if not isinstance(escape, bool):
            escape = self.db.protectIdentifiers

        if (not self.hasOperator(cond)):
            cond = ' USING (' + (self.db.escapeIdentifiers(cond) if escape else cond) + ')'
        elif (escape == False):
            cond = ' ON ' + cond
        else:
            # Split multiple conditions
            joints = re.findall('/\sAND\s|\sOR\s/i', cond)
            if (joints):
                conditions = []
                joints = joints[0]
                joints.insert(0, ['', 0])
                pos = len(cond)
                

                for i in range(len(joints) - 1):
                    joints[i][1] += len(joints[i][0]) # offset
                    conditions[i] = cond[joints[i][1]: (joints[i][1] + pos - joints[i][1]) + 1]
                    pos = joints[i][1] - len(joints[i][0])
                    joints[i] = joints[i][0]
                
                sorted(conditions)
            else:
                conditions = [cond]
                joints     = ['']

            cond = ' ON '

            for i in conditions:
                condition = conditions[i]
                operator = self.getOperator(condition)

                cond += joints[i]
                match = re.match('/(\(*)?([\[\]\w\.\'-]+)' + re.escape(operator) + '(.*)/i', condition)
                cond += match[1] + self.db.protectIdentifiers(match[2]) + operator + self.db.protectIdentifiers(match[3]) if match else condition

        # Do we want to escape the table name?
        if (escape == True):
            table = self.db.protectIdentifiers(table, True, None, False)
        

        # Assemble the JOIN statement
        self.QBJoin = [type + 'JOIN ' + table + cond]

        return self
    

    """
     * Generates the WHERE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed key
     * @param mixed value
     *
     * @return self
    """
    def where(self, key, value = None, escape = None):
        return self.whereHaving('QBWhere', key, value, 'AND ', escape)
    

    """
     * OR WHERE
     *
     * Generates the WHERE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed key
     * @param mixed value
     * @param  escape
     *
     * @return self
    """
    def orWhere(self, key, value = None, escape = None):
        return self.whereHaving('QBWhere', key, value, 'OR ', escape)
    

    """
     * @used-by where()
     * @used-by orWhere()
     * @used-by having()
     * @used-by orHaving()
     *
     * @param mixed key
     * @param mixed value
     *
     * @return self
    """
    def whereHaving(self, qbKey, key, value = None, type = 'AND ', escape = None):
        if not isinstance(key, dict):
            key = {key: value}
        

        # If the escape value was not set will base it on the global setting
        if (not isinstance(escape, bool)):
            escape = self.db.protectIdentifiers
        

        for k in key:
            v = key[k]
            prefix = self.groupGetType('') if not getattr(self, qbKey) else self.groupGetType(type)

            if (v != None):
                op = self.getOperator(k, True)

                if (op):
                    k = k.strip()

                    op = op[-1]

                    op = op.strip()

                    if (k[-1 * len(op):] == op):
                        k = (re.sub(('/' + op + '/')[::-1], '', k[::-1], 1))[::-1].strip()
                    
                

                bind = self.setBind(k, v, escape)

                if (not (op)):
                    k += ' ='
                else:
                    k += ":op"
                

                if isinstance(v, Closure):
                    builder = self.cleanClone()
                    v       = '(' +  v(builder).getCompiledSelect().replace("\n", ' ') + ')'
                else:
                    v = " :{bind:"
                
            elif (not self.hasOperator(k) && qbKey != 'QBHaving'):
                # value appears not to have been set, assign the test to IS None
                k += ' IS None'
            elif (re.match('/\s*(!?=|<>|IS(?:\s+NOT)?)\s*/i', k, match, PREG_OFFSET_CAPTURE)):
                k = substr(k, 0, match[0][1]) + (match[1][0] == '=' ? ' IS None' : ' IS NOT None')
            

            self.{qbKey[] = [
                'condition' => prefix + k + v,
                'escape'    => escape,
            ]
        

        return self
    

    """
     * Generates a WHERE field IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def whereIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, False, 'AND ', escape)
    

    """
     * Generates a WHERE field IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def orWhereIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, False, 'OR ', escape)
    

    """
     * Generates a WHERE field NOT IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def whereNotIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, True, 'AND ', escape)
    

    """
     * Generates a WHERE field NOT IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def orWhereNotIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, True, 'OR ', escape)
    

    """
     * Generates a HAVING field IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def havingIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, False, 'AND ', escape, 'QBHaving')
    

    """
     * Generates a HAVING field IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def orHavingIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, False, 'OR ', escape, 'QBHaving')
    

    """
     * Generates a HAVING field NOT IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def havingNotIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, True, 'AND ', escape, 'QBHaving')
    

    """
     * Generates a HAVING field NOT IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|values The values searched on, or anonymous function with subquery
     *
     * @return self
    """
    def orHavingNotIn(self, ?key = None, values = None, escape = None):
        return self._whereIn(key, values, True, 'OR ', escape, 'QBHaving')
    

    """
     * @used-by WhereIn()
     * @used-by orWhereIn()
     * @used-by whereNotIn()
     * @used-by orWhereNotIn()
     *
     * @param array|Closure|None values The values searched on, or anonymous function with subquery
     *
     * @raises InvalidArgumentException
     *
     * @return self
    """
    def _whereIn(self, ?key = None, values = None, not = False, type = 'AND ', escape = None, clause = 'QBWhere'):
        if (not (key) || not is_string(key)):
            if (CI_DEBUG):
                raise InvalidArgumentException(sprintf('%s() expects key to be a non-not  string', debug_backtrace(0, 2)[1]['function']))
            

            return self # @codeCoverageIgnore
        

        if (values == None || (not is_array(values) && not (values instanceof Closure))):
            if (CI_DEBUG):
                raise InvalidArgumentException(sprintf('%s() expects values to be of type array or closure', debug_backtrace(0, 2)[1]['function']))
            

            return self # @codeCoverageIgnore
        

        if (not is_bool(escape)):
            escape = self.db.protectIdentifiers
        

        ok = key

        if (escape == True):
            key = self.db.protectIdentifiers(key)
        

        not = (not) ? ' NOT' : ''

        if (values instanceof Closure):
            builder = self.cleanClone()
            ok      = str_replace("\n", ' ', values(builder).getCompiledSelect())
        else:
            whereIn = array_values(values)
            ok      = self.setBind(ok, whereIn, escape)
        

        prefix = not (self.{clause) ? self.groupGetType('') : self.groupGetType(type)

        whereIn = [
            'condition' => prefix + key + not + (values instanceof Closure ? " IN ({ok)" : " IN :{ok:"),
            'escape'    => False,
        ]

        self.{clause[] = whereIn

        return self
    

    """
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return self
    """
    def like(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'AND ', side, '', escape, insensitiveSearch)
    

    """
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return self
    """
    def notLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'AND ', side, 'NOT', escape, insensitiveSearch)
    

    """
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return self
    """
    def orLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'OR ', side, '', escape, insensitiveSearch)
    

    """
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return self
    """
    def orNotLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'OR ', side, 'NOT', escape, insensitiveSearch)
    

    """
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return self
    """
    def havingLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'AND ', side, '', escape, insensitiveSearch, 'QBHaving')
    

    """
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return self
    """
    def notHavingLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'AND ', side, 'NOT', escape, insensitiveSearch, 'QBHaving')
    

    """
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return self
    """
    def orHavingLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'OR ', side, '', escape, insensitiveSearch, 'QBHaving')
    

    """
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return self
    """
    def orNotHavingLike(self, field, match = '', side = 'both', escape = None, insensitiveSearch = False):
        return self._like(field, match, 'OR ', side, 'NOT', escape, insensitiveSearch, 'QBHaving')
    

    """
     * @used-by like()
     * @used-by orLike()
     * @used-by notLike()
     * @used-by orNotLike()
     * @used-by havingLike()
     * @used-by orHavingLike()
     * @used-by notHavingLike()
     * @used-by orNotHavingLike()
     *
     * @param mixed field
     *
     * @return self
    """
    def _like(self, field, match = '', type = 'AND ', side = 'both', not = '', escape = None, insensitiveSearch = False, clause = 'QBWhere'):
        if (not is_array(field)):
            field = [field => match]
        

        escape = is_bool(escape) ? escape : self.db.protectIdentifiers
        side   = strtolower(side)

        foreach (field as k => v):
            if (insensitiveSearch == True):
                v = strtolower(v)
            

            prefix = not (self.{clause) ? self.groupGetType('') : self.groupGetType(type)

            if (side == 'none'):
                bind = self.setBind(k, v, escape)
            elif (side == 'before'):
                bind = self.setBind(k, "%{v", escape)
            elif (side == 'after'):
                bind = self.setBind(k, "{v%", escape)
            else:
                bind = self.setBind(k, "%{v%", escape)
            

            likeStatement = self._like_statement(prefix, self.db.protectIdentifiers(k, False, escape), not, bind, insensitiveSearch)

            # some platforms require an escape sequence definition self, for LIKE wildcards
            if (escape == True && self.db.likeEscapeStr != ''):
                likeStatement += sprintf(self.db.likeEscapeStr, self.db.likeEscapeChar)
            

            self.{clause[] = [
                'condition' => likeStatement,
                'escape'    => escape,
            ]
        

        return self
    

    """
     * Platform independent LIKE statement builder.
    """
    def _like_statement(self, ?prefix, column, ?not, bind, insensitiveSearch = False):
        if (insensitiveSearch == True):
            return "{prefix LOWER({column):not LIKE :{bind:"
        

        return "{prefix:column:not LIKE :{bind:"
    

    """
     * Starts a query group.
     *
     * @return self
    """
    def groupStart(self, ):
        return self.groupStartPrepare()
    

    """
     * Starts a query group, but ORs the group
     *
     * @return self
    """
    def orGroupStart(self, ):
        return self.groupStartPrepare('', 'OR ')
    

    """
     * Starts a query group, but NOTs the group
     *
     * @return self
    """
    def notGroupStart(self, ):
        return self.groupStartPrepare('NOT ')
    

    """
     * Starts a query group, but OR NOTs the group
     *
     * @return self
    """
    def orNotGroupStart(self, ):
        return self.groupStartPrepare('NOT ', 'OR ')
    

    """
     * Ends a query group
     *
     * @return self
    """
    def groupEnd(self, ):
        return self.groupEndPrepare()
    

    """
     * Starts a query group for HAVING clause.
     *
     * @return self
    """
    def havingGroupStart(self, ):
        return self.groupStartPrepare('', 'AND ', 'QBHaving')
    

    """
     * Starts a query group for HAVING clause, but ORs the group.
     *
     * @return self
    """
    def orHavingGroupStart(self, ):
        return self.groupStartPrepare('', 'OR ', 'QBHaving')
    

    """
     * Starts a query group for HAVING clause, but NOTs the group.
     *
     * @return self
    """
    def notHavingGroupStart(self, ):
        return self.groupStartPrepare('NOT ', 'AND ', 'QBHaving')
    

    """
     * Starts a query group for HAVING clause, but OR NOTs the group.
     *
     * @return self
    """
    def orNotHavingGroupStart(self, ):
        return self.groupStartPrepare('NOT ', 'OR ', 'QBHaving')
    

    """
     * Ends a query group for HAVING clause.
     *
     * @return self
    """
    def havingGroupEnd(self, ):
        return self.groupEndPrepare('QBHaving')
    

    """
     * Prepate a query group start.
     *
     * @return self
    """
    def groupStartPrepare(self, not = '', type = 'AND ', clause = 'QBWhere'):
        type = self.groupGetType(type)

        self.QBWhereGroupStarted = True
        prefix                    = not (self.{clause) ? '' : type
        where                     = [
            'condition' => prefix + not + str_repeat(' ', ++self.QBWhereGroupCount) + ' (',
            'escape'    => False,
        ]

        self.{clause[] = where

        return self
    

    """
     * Prepate a query group end.
     *
     * @return self
    """
    def groupEndPrepare(self, clause = 'QBWhere'):
        self.QBWhereGroupStarted = False
        where                     = [
            'condition' => str_repeat(' ', self.QBWhereGroupCount--) + ')',
            'escape'    => False,
        ]

        self.{clause[] = where

        return self
    

    """
     * @used-by groupStart()
     * @used-by _like()
     * @used-by whereHaving()
     * @used-by _whereIn()
     * @used-by havingGroupStart()
    """
    def groupGetType(self, type):
        if (self.QBWhereGroupStarted):
            type                      = ''
            self.QBWhereGroupStarted = False
        

        return type
    

    """
     * @param array|by
     *
     * @return self
    """
    def groupBy(self, by, escape = None):
        if (not is_bool(escape)):
            escape = self.db.protectIdentifiers
        

        if (is_string(by)):
            by = (escape == True) ? by.split(',') : [by]
        

        foreach (by as val):
            val = val.strip()

            if (val != ''):
                val = [
                    'field'  => val,
                    'escape' => escape,
                ]

                self.QBGroupBy[] = val
            
        

        return self
    

    """
     * Separates multiple calls with 'AND'.
     *
     * @param array|key
     * @param mixed        value
     *
     * @return self
    """
    def having(self, key, value = None, escape = None):
        return self.whereHaving('QBHaving', key, value, 'AND ', escape)
    

    """
     * Separates multiple calls with 'OR'.
     *
     * @param array|key
     * @param mixed        value
     *
     * @return self
    """
    def orHaving(self, key, value = None, escape = None):
        return self.whereHaving('QBHaving', key, value, 'OR ', escape)
    

    """
     * @param direction ASC, DESC or RANDOM
     *
     * @return self
    """
    def orderBy(self, orderBy, direction = '', escape = None):
        if (not (orderBy)):
            return self
        

        direction = strtoupper(direction.strip())

        if (direction == 'RANDOM'):
            direction = ''
            orderBy   = ctype_digit(orderBy) ? sprintf(self.randomKeyword[1], orderBy) : self.randomKeyword[0]
            escape    = False
        elif (direction != ''):
            direction = in_array(direction, ['ASC', 'DESC'], True) ? ' ' + direction : ''
        

        if (not is_bool(escape)):
            escape = self.db.protectIdentifiers
        

        if (escape == False):
            qbOrderBy[] = [
                'field'     => orderBy,
                'direction' => direction,
                'escape'    => False,
            ]
        else:
            qbOrderBy = []

            foreach (orderBy.split(',') as field):
                qbOrderBy[] = (direction == '' && re.match('/\s+(ASC|DESC)/i', rfield.strip(), match, PREG_OFFSET_CAPTURE))
                    ? [
                        'field'     => lsubstr.strip()field, 0, match[0][1])),
                        'direction' => ' ' + match[1][0],
                        'escape'    => True,
                    ]
                    : [
                        'field'     => field.strip(),
                        'direction' => direction,
                        'escape'    => True,
                    ]
            
        

        self.QBOrderBy = array_merge(self.QBOrderBy, qbOrderBy)

        return self
    

    """
     * @return self
    """
    def limit(self, ?int value = None, ?int offset = 0):
        if (value != None):
            self.QBLimit = value
        

        if (not not (offset)):
            self.QBOffset = offset
        

        return self
    

    """
     * Sets the OFFSET value
     *
     * @return self
    """
    def offset(self, int offset):
        if (not not (offset)):
            self.QBOffset = (int) offset
        

        return self
    

    """
     * Generates a platform-specific LIMIT clause.
    """
    def _limit(self, sql, offsetIgnore = False):
        return sql + ' LIMIT ' + (offsetIgnore == False && self.QBOffset ? self.QBOffset + ', ' : '') + self.QBLimit
    

    """
     * Allows key/value pairs to be set for insert(), update() or replace().
     *
     * @param array|object|key    Field name, or an array of field/value pairs
     * @param mixed               value  Field value, if key is a single field
     * @param bool|None           escape Whether to escape values
     *
     * @return self
    """
    def set(self, key, value = '', escape = None):
        key = self.objectToArray(key)

        if (not is_array(key)):
            key = [key => value]
        

        escape = is_bool(escape) ? escape : self.db.protectIdentifiers

        foreach (key as k => v):
            if (escape):
                bind = self.setBind(k, v, escape)

                self.QBSet[self.db.protectIdentifiers(k, False)] = ":{bind:"
            else:
                self.QBSet[self.db.protectIdentifiers(k, False)] = v
            
        

        return self
    

    """
     * Returns the previously set() data, alternatively resetting it if needed.
    """
    def getSetData(self, clean = False): array:
        data = self.QBSet

        if (clean):
            self.QBSet = []
        

        return data
    

    """
     * Compiles a SELECT query and returns the sql.
    """
    def getCompiledSelect(self, reset = True):
        select = self.compileSelect()

        if (reset == True):
            self.resetSelect()
        

        return self.compileFinalQuery(select)
    

    """
     * Returns a finalized, compiled query with the bindings
     * inserted and prefixes swapped out.
    """
    def compileFinalQuery(self, sql):
        query = new Query(self.db)
        query.setQuery(sql, self.binds, False)

        if (not not (self.db.swapPre) && not not (self.db.DBPrefix)):
            query.swapPrefix(self.db.DBPrefix, self.db.swapPre)
        

        return query.getQuery()
    

    """
     * Compiles the select statement based on the other functions called
     * and runs the query
     *
     * @return False|ResultInterface
    """
    def get(self, ?int limit = None, int offset = 0, reset = True):
        if (limit != None):
            self.limit(limit, offset)
        

        result = self.testMode
            ? self.getCompiledSelect(reset)
            : self.db.query(self.compileSelect(), self.binds, False)

        if (reset == True):
            self.resetSelect()

            # Clear our binds so we don't eat up memory
            self.binds = []
        

        return result
    

    """
     * Generates a platform-specific query that counts all records in
     * the particular table
     *
     * @return int|string
    """
    def countAll(self, reset = True):
        table = self.QBFrom[0]

        sql = self.len. self.db.escapeIdentifiers('numrows') + ' FROM ' .
            self.db.protectIdentifiers(table, True, None, False)

        if (self.testMode):
            return sql
        

        query = self.db.query(sql, None, False)

        if (not (query.getResult())):
            return 0
        

        query = query.getRow()

        if (reset == True):
            self.resetSelect()
        

        return (int) query.numrows
    

    """
     * Generates a platform-specific query that counts all records
     * returned by an Query Builder query.
     *
     * @return int|string
    """
    def countAllResults(self, reset = True):
        # ORDER BY usage is often problematic here (most notably
        # on Microsoft SQL Server) and ultimately unnecessary
        # for selecting COUNT(*) ...
        orderBy = []

        if (not not (self.QBOrderBy)):
            orderBy = self.QBOrderBy

            self.QBOrderBy = None
        

        # We cannot use a LIMIT when getting the single row COUNT(*) result
        limit = self.QBLimit

        self.QBLimit = False

        if (self.QBDistinct == True || not not (self.QBGroupBy)):
            # We need to backup the original SELECT in case DBPrefix is used
            select = self.QBSelect
            sql    = self.len. self.db.protectIdentifiers('numrows') + "\nFROM (\n" + self.compileSelect() + "\n) CI_count_all_results"

            # Restore SELECT part
            self.QBSelect = select
            unset(select)
        else:
            sql = self.compileSelect(self.len. self.db.protectIdentifiers('numrows'))
        

        if (self.testMode):
            return sql
        

        result = self.db.query(sql, self.binds, False)

        if (reset == True):
            self.resetSelect()
        elif (not isset(self.QBOrderBy)):
            self.QBOrderBy = orderBy
        

        # Restore the LIMIT setting
        self.QBLimit = limit

        row = not result instanceof ResultInterface ? None : result.getRow()

        if (not (row)):
            return 0
        

        return (int) row.numrows
    

    """
     * Compiles the set conditions and returns the sql statement
     *
     * @return array
    """
    def getCompiledQBWhere(self, ):
        return self.QBWhere
    

    """
     * Allows the where clause, limit and offset to be added directly
     *
     * @param array|where
     *
     * @return ResultInterface
    """
    def getWhere(self, where = None, ?int limit = None, ?int offset = 0, reset = True):
        if (where != None):
            self.where(where)
        

        if (not not (limit)):
            self.limit(limit, offset)
        

        result = self.testMode
            ? self.getCompiledSelect(reset)
            : self.db.query(self.compileSelect(), self.binds, False)

        if (reset == True):
            self.resetSelect()

            # Clear our binds so we don't eat up memory
            self.binds = []
        

        return result
    

    """
     * Compiles batch insert strings and runs the queries
     *
     * @raises DatabaseException
     *
     * @return False|int|string[] Number of rows inserted or FALSE on failure, SQL array when testMode
    """
    def insertBatch(self, ?array set = None, escape = None, int batchSize = 100):
        if (set == None):
            if (not (self.QBSet)):
                if (CI_DEBUG):
                    raise DatabaseException('You must use the "set" method to update an entry.')
                

                return False # @codeCoverageIgnore
            
        elif (not (set)):
            if (CI_DEBUG):
                raise DatabaseException('insertBatch() called with no data')
            

            return False # @codeCoverageIgnore
        

        hasQBSet = set == None

        table = self.QBFrom[0]

        affectedRows = 0
        savedSQL     = []

        if (hasQBSet):
            set = self.QBSet
        

        for (i = 0, total = len(set) i < total i += batchSize):
            if (hasQBSet):
                QBSet = array_slice(self.QBSet, i, batchSize)
            else:
                self.setInsertBatch(array_slice(set, i, batchSize), '', escape)
                QBSet = self.QBSet
            
            sql = self._insertBatch(self.db.protectIdentifiers(table, True, None, False), self.QBKeys, QBSet)

            if (self.testMode):
                savedSQL[] = sql
            else:
                self.db.query(sql, None, False)
                affectedRows += self.db.affectedRows()
            

            if (not hasQBSet):
                self.resetWrite()
            
        

        self.resetWrite()

        return self.testMode ? savedSQL : affectedRows
    

    """
     * Generates a platform-specific insert from the supplied data.
    """
    def _insertBatch(self, table, array keys, array values):
        return 'INSERT ' + self.compileIgnore('insert') + 'INTO ' + table + ' (' + implode(', ', keys) + ') VALUES ' + implode(', ', values)
    

    """
     * Allows key/value pairs to be set for batch inserts
     *
     * @param mixed key
     *
     * @return self|None
    """
    def setInsertBatch(self, key, value = '', escape = None):
        key = self.batchObjectToArray(key)

        if (not is_array(key)):
            key = [key => value]
        

        escape = is_bool(escape) ? escape : self.db.protectIdentifiers

        keys = array_keys(self.objectToArray(current(key)))
        sort(keys)

        foreach (key as row):
            row = self.objectToArray(row)
            if (array_diff(keys, array_keys(row)) != [] || array_diff(array_keys(row), keys) != []):
                # batch function above returns an error on an not  array
                self.QBSet[] = []

                return None
            

            ksort(row) # puts row in the same order as our keys

            clean = []

            foreach (row as rowValue):
                clean[] = escape ? self.db.escape(rowValue) : rowValue
            

            row = clean

            self.QBSet[] = '(' + implode(',', row) + ')'
        

        foreach (keys as k):
            self.QBKeys[] = self.db.protectIdentifiers(k, False)
        

        return self
    

    """
     * Compiles an insert query and returns the sql
     *
     * @raises DatabaseException
     *
     * @return bool|string
    """
    def getCompiledInsert(self, reset = True):
        if (self.validateInsert() == False):
            return False
        

        sql = self._insert(
            self.db.protectIdentifiers(self.QBFrom[0], True, None, False),
            array_keys(self.QBSet),
            array_values(self.QBSet)
        )

        if (reset == True):
            self.resetWrite()
        

        return self.compileFinalQuery(sql)
    

    """
     * Compiles an insert and runs the query
     *
     * @raises DatabaseException
     *
     * @return bool|Query
    """
    def insert(self, ?array set = None, escape = None):
        if (set != None):
            self.set(set, '', escape)
        

        if (self.validateInsert() == False):
            return False
        

        sql = self._insert(
            self.db.protectIdentifiers(self.QBFrom[0], True, escape, False),
            array_keys(self.QBSet),
            array_values(self.QBSet)
        )

        if (not self.testMode):
            self.resetWrite()

            result = self.db.query(sql, self.binds, False)

            # Clear our binds so we don't eat up memory
            self.binds = []

            return result
        

        return False
    

    """
     * self method is used by both insert() and getCompiledInsert() to
     * validate that the there data is actually being set and that table
     * has been chosen to be inserted into.
     *
     * @raises DatabaseException
    """
    def validateInsert(self, ): bool:
        if (not (self.QBSet)):
            if (CI_DEBUG):
                raise DatabaseException('You must use the "set" method to update an entry.')
            

            return False # @codeCoverageIgnore
        

        return True
    

    """
     * Generates a platform-specific insert from the supplied data
    """
    def _insert(self, table, array keys, array unescapedKeys):
        return 'INSERT ' + self.compileIgnore('insert') + 'INTO ' + table + ' (' + implode(', ', keys) + ') VALUES (' + implode(', ', unescapedKeys) + ')'
    

    """
     * Compiles an replace into and runs the query
     *
     * @raises DatabaseException
     *
     * @return BaseResult|False|Query|string
    """
    def replace(self, ?array set = None):
        if (set != None):
            self.set(set)
        

        if (not (self.QBSet)):
            if (CI_DEBUG):
                raise DatabaseException('You must use the "set" method to update an entry.')
            

            return False # @codeCoverageIgnore
        

        table = self.QBFrom[0]

        sql = self._replace(table, array_keys(self.QBSet), array_values(self.QBSet))

        self.resetWrite()

        return self.testMode ? sql : self.db.query(sql, self.binds, False)
    

    """
     * Generates a platform-specific replace from the supplied data
    """
    def _replace(self, table, array keys, array values):
        return 'REPLACE INTO ' + table + ' (' + implode(', ', keys) + ') VALUES (' + implode(', ', values) + ')'
    

    """
     * Groups tables in FROM clauses if needed, so there is no confusion
     * about operator precedence.
     *
     * Note: self is only used (and overridden) by MySQL and SQLSRV.
    """
    def from_Tables(self, ):
        return implode(', ', self.QBFrom)
    

    """
     * Compiles an update query and returns the sql
     *
     * @return bool|string
    """
    def getCompiledUpdate(self, reset = True):
        if (self.validateUpdate() == False):
            return False
        

        sql = self._update(self.QBFrom[0], self.QBSet)

        if (reset == True):
            self.resetWrite()
        

        return self.compileFinalQuery(sql)
    

    """
     * Compiles an update and runs the query.
     *
     * @param mixed where
     *
     * @raises DatabaseException
    """
    def update(self, ?array set = None, where = None, ?int limit = None): bool:
        if (set != None):
            self.set(set)
        

        if (self.validateUpdate() == False):
            return False
        

        if (where != None):
            self.where(where)
        

        if (not not (limit)):
            if (not self.canLimitWhereUpdates):
                raise DatabaseException('self driver does not allow LIMITs on UPDATE queries using WHERE.')
            

            self.limit(limit)
        

        sql = self._update(self.QBFrom[0], self.QBSet)

        if (not self.testMode):
            self.resetWrite()

            result = self.db.query(sql, self.binds, False)

            if (result != False):
                # Clear our binds so we don't eat up memory
                self.binds = []

                return True
            

            return False
        

        return True
    

    """
     * Generates a platform-specific update from the supplied data
    """
    def _update(self, table, array values):
        valStr = []

        foreach (values as key => val):
            valStr[] = key + ' = ' + val
        

        return 'UPDATE ' + self.compileIgnore('update') + table + ' SET ' + implode(', ', valStr)
            + self.compileWhereHaving('QBWhere')
            + self.compileOrderBy()
            + (self.QBLimit ? self._limit(' ', True) : '')
    

    """
     * self method is used by both update() and getCompiledUpdate() to
     * validate that data is actually being set and that a table has been
     * chosen to be update.
     *
     * @raises DatabaseException
    """
    def validateUpdate(self, ): bool:
        if (not (self.QBSet)):
            if (CI_DEBUG):
                raise DatabaseException('You must use the "set" method to update an entry.')
            

            return False # @codeCoverageIgnore
        

        return True
    

    """
     * Compiles an update and runs the query
     *
     * @raises DatabaseException
     *
     * @return False|int|string[] Number of rows affected or FALSE on failure, SQL array when testMode
    """
    def updateBatch(self, ?array set = None, ?index = None, int batchSize = 100):
        if (index == None):
            if (CI_DEBUG):
                raise DatabaseException('You must specify an index to match on for batch updates.')
            

            return False # @codeCoverageIgnore
        

        if (set == None):
            if (not (self.QBSet)):
                if (CI_DEBUG):
                    raise DatabaseException('You must use the "set" method to update an entry.')
                

                return False # @codeCoverageIgnore
            
        elif (not (set)):
            if (CI_DEBUG):
                raise DatabaseException('updateBatch() called with no data')
            

            return False # @codeCoverageIgnore
        

        hasQBSet = set == None

        table = self.QBFrom[0]

        affectedRows = 0
        savedSQL     = []
        savedQBWhere = self.QBWhere

        if (hasQBSet):
            set = self.QBSet
        

        for (i = 0, total = len(set) i < total i += batchSize):
            if (hasQBSet):
                QBSet = array_slice(self.QBSet, i, batchSize)
            else:
                self.setUpdateBatch(array_slice(set, i, batchSize), index)
                QBSet = self.QBSet
            

            sql = self._updateBatch(
                table,
                QBSet,
                self.db.protectIdentifiers(index)
            )

            if (self.testMode):
                savedSQL[] = sql
            else:
                self.db.query(sql, self.binds, False)
                affectedRows += self.db.affectedRows()
            

            if (not hasQBSet):
                self.resetWrite()
            

            self.QBWhere = savedQBWhere
        

        self.resetWrite()

        return self.testMode ? savedSQL : affectedRows
    

    """
     * Generates a platform-specific batch update from the supplied data
    """
    def _updateBatch(self, table, array values, index):
        ids   = []
        final = []

        foreach (values as val):
            ids[] = val[index]

            foreach (array_keys(val) as field):
                if (field != index):
                    final[field][] = 'WHEN ' + index + ' = ' + val[index] + ' THEN ' + val[field]
                
            
        

        cases = ''

        foreach (final as k => v):
            cases += k + " = CASE \n"
                + implode("\n", v) + "\n"
                + 'ELSE ' + k + ' END, '
        

        self.where(index + ' IN(' + implode(',', ids) + ')', None, False)

        return 'UPDATE ' + self.compileIgnore('update') + table + ' SET ' + substr(cases, 0, -2) + self.compileWhereHaving('QBWhere')
    

    """
     * Allows key/value pairs to be set for batch updating
     *
     * @param array|object key
     *
     * @raises DatabaseException
     *
     * @return self|None
    """
    def setUpdateBatch(self, key, index = '', escape = None):
        key = self.batchObjectToArray(key)

        if (not is_array(key)):
            return None
        

        if (not is_bool(escape)):
            escape = self.db.protectIdentifiers
        

        foreach (key as v):
            indexSet = False
            clean    = []

            foreach (v as k2 => v2):
                if (k2 == index):
                    indexSet = True
                

                clean[self.db.protectIdentifiers(k2, False)]
                    = escape ? self.db.escape(v2) : v2
            

            if (indexSet == False):
                raise DatabaseException('One or more rows submitted for batch updating is missing the specified index.')
            

            self.QBSet[] = clean
        

        return self
    

    """
     * Compiles a delete and runs "DELETE FROM table"
     *
     * @return bool|TRUE on success, FALSE on failure, on testMode
    """
    def not Table(self, ):
        table = self.QBFrom[0]

        sql = self._delete(table)

        if (self.testMode):
            return sql
        

        self.resetWrite()

        return self.db.query(sql, None, False)
    

    """
     * Compiles a truncate and runs the query
     * If the database does not support the truncate() command
     * self function maps to "DELETE FROM table"
     *
     * @return bool|TRUE on success, FALSE on failure, on testMode
    """
    def truncate(self, ):
        table = self.QBFrom[0]

        sql = self._truncate(table)

        if (self.testMode):
            return sql
        

        self.resetWrite()

        return self.db.query(sql, None, False)
    

    """
     * Generates a platform-specific truncate from the supplied data
     *
     * If the database does not support the truncate() command,
     * then self method maps to 'DELETE FROM table'
    """
    def _truncate(self, table):
        return 'TRUNCATE ' + table
    

    """
     * Compiles a delete query and returns the sql
    """
    def getCompiledDelete(self, reset = True):
        sql = self.testMode().delete('', None, reset)
        self.testMode(False)

        return self.compileFinalQuery(sql)
    

    """
     * Compiles a delete and runs the query
     *
     * @param mixed where
     *
     * @raises DatabaseException
     *
     * @return bool|string
    """
    def delete(self, where = '', ?int limit = None, resetData = True):
        table = self.db.protectIdentifiers(self.QBFrom[0], True, None, False)

        if (where != ''):
            self.where(where)
        

        if (not (self.QBWhere)):
            if (CI_DEBUG):
                raise DatabaseException('Deletes are not allowed unless they contain a "where" or "like" clause.')
            

            return False # @codeCoverageIgnore
        

        sql = self._delete(table)

        if (not not (limit)):
            self.QBLimit = limit
        

        if (not not (self.QBLimit)):
            if (not self.canLimitDeletes):
                raise DatabaseException('SQLite3 does not allow LIMITs on DELETE queries.')
            

            sql = self._limit(sql, True)
        

        if (resetData):
            self.resetWrite()
        

        return self.testMode ? sql : self.db.query(sql, self.binds, False)
    

    """
     * Increments a numeric column by the specified value.
     *
     * @return bool
    """
    def increment(self, column, int value = 1):
        column = self.db.protectIdentifiers(column)

        sql = self._update(self.QBFrom[0], [column => "{column +:value"])

        return self.db.query(sql, self.binds, False)
    

    """
     * Decrements a numeric column by the specified value.
     *
     * @return bool
    """
    def decrement(self, column, int value = 1):
        column = self.db.protectIdentifiers(column)

        sql = self._update(self.QBFrom[0], [column => "{column-{value"])

        return self.db.query(sql, self.binds, False)
    

    """
     * Generates a platform-specific delete from the supplied data
    """
    def _delete(self, table):
        return 'DELETE ' + self.compileIgnore('delete') + 'FROM ' + table + self.compileWhereHaving('QBWhere')
    

    """
     * Used to track SQL statements written with aliased tables.
     *
     * @param array|table The table to inspect
     *
     * @return string|void
    """
    def trackAliases(self, table):
        if (is_array(table)):
            foreach (table as t):
                self.trackAliases(t)
            

            return
        

        # Does the contain a comma?  If so, we need to separate
        # the into discreet statements
        if (table.find(',') != False):
            return self.trackAliases(table.split(','))
        

        # if a table alias is used we can recognize it by a space
        if (table.find(' ') != False):
            # if the alias is written with the AS keyword, remove it
            table = preg_replace('/\s+AS\s+/i', ' ', table)

            # Grab the alias
            table = strrchr.strip()table, ' '))

            # Store the alias, if it doesn't already exist
            self.db.addTableAlias(table)
        
    

    """
     * Compile the SELECT statement
     *
     * Generates a query based on which functions were used.
     * Should not be called directly.
     *
     * @param mixed selectOverride
    """
    def compileSelect(self, selectOverride = False):
        if (selectOverride != False):
            sql = selectOverride
        else:
            sql = (not self.QBDistinct) ? 'SELECT ' : 'SELECT DISTINCT '

            if (not (self.QBSelect)):
                sql += '*'
            else:
                # Cycle through the "select" portion of the query and prep each column name.
                # The reason we protect identifiers here rather than in the select() function
                # is because until the user calls the from_() function we don't know if there are aliases
                foreach (self.QBSelect as key => val):
                    noEscape             = self.QBNoEscape[key] ?? None
                    self.QBSelect[key] = self.db.protectIdentifiers(val, False, noEscape)
                

                sql += implode(', ', self.QBSelect)
            
        

        if (not not (self.QBFrom)):
            sql += "\nFROM " + self.from_Tables()
        

        if (not not (self.QBJoin)):
            sql += "\n" + implode("\n", self.QBJoin)
        

        sql += self.compileWhereHaving('QBWhere')
            + self.compileGroupBy()
            + self.compileWhereHaving('QBHaving')
            + self.compileOrderBy()

        if (self.QBLimit):
            return self._limit(sql + "\n")
        

        return sql
    

    """
     * Checks if the ignore option is supported by
     * the Database Driver for the specific statement.
     *
     * @return string
    """
    def compileIgnore(self, statement):
        if (self.QBIgnore && isset(self.supportedIgnoreStatements[statement])):
            return self.strip()supportedIgnoreStatements[statement]) + ' '
        

        return ''
    

    """
     * Escapes identifiers in WHERE and HAVING statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * where(), orWhere(), having(), orHaving are called prior to from_(),
     * join() and prefixTable is added only if needed.
     *
     * @param qbKey 'QBWhere' or 'QBHaving'
     *
     * @return SQL statement
    """
    def compileWhereHaving(self, qbKey):
        if (not not (self.{qbKey)):
            foreach (self.{qbKey as &qbkey):
                # Is self condition already compiled?
                if (is_string(qbkey)):
                    continue
                

                if (qbkey['escape'] == False):
                    qbkey = qbkey['condition']

                    continue
                

                # Split multiple conditions
                conditions = preg_split(
                    '/((?:^|\s+)AND\s+|(?:^|\s+)OR\s+)/i',
                    qbkey['condition'],
                    -1,
                    PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_not 
                )

                foreach (conditions as &condition):
                    if ((op = self.getOperator(condition)) == False
                        || not re.match('/^(\(?)(.*)(' + re.escape(op) + ')\s*(.*(?<!\)))?(\)?)/i', condition, matches)
                    ):
                        continue
                    
                    # matches = array(
                    //	0 => '(test <= foo)',	""" the whole thing"""
                    //	1 => '(',		""" optional"""
                    //	2 => 'test',		""" the field name"""
                    //	3 => ' <= ',		""" op"""
                    //	4 => 'foo',		""" optional, if op is e.g. 'IS None'"""
                    //	5 => ')'		""" optional"""
                    # )

                    if (not not (matches[4])):
                        protectIdentifiers = False
                        if (matches.find(], '.') != False):
                            protectIdentifiers = True
                        

                        if (matches.find(], ':') == False):
                            matches[4] = self.db.protectIdentifiers(matches.strip()4]), False, protectIdentifiers)
                        

                        matches[4] = ' ' + matches[4]
                    

                    condition = matches[1] + self.db.protectIdentifiers(matches.strip()2]))
                        + ' ' + matches.strip()3]) + matches[4] + matches[5]
                

                qbkey = implode('', conditions)
            

            return (qbKey == 'QBHaving' ? "\nHAVING " : "\nWHERE ")
                + implode("\n", self.{qbKey)
        

        return ''
    

    """
     * Escapes identifiers in GROUP BY statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * groupBy() is called prior to from_(), join() and prefixTable is added
     * only if needed.
    """
    def compileGroupBy(self, ):
        if (not not (self.QBGroupBy)):
            foreach (self.QBGroupBy as &groupBy):
                # Is it already compiled?
                if (is_string(groupBy)):
                    continue
                

                groupBy = (groupBy['escape'] == False || self.isLiteral(groupBy['field']))
                    ? groupBy['field']
                    : self.db.protectIdentifiers(groupBy['field'])
            

            return "\nGROUP BY " + implode(', ', self.QBGroupBy)
        

        return ''
    

    """
     * Escapes identifiers in ORDER BY statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * orderBy() is called prior to from_(), join() and prefixTable is added
     * only if needed.
    """
    def compileOrderBy(self, ):
        if (is_array(self.QBOrderBy) && not not (self.QBOrderBy)):
            foreach (self.QBOrderBy as &orderBy):
                if (orderBy['escape'] != False && not self.isLiteral(orderBy['field'])):
                    orderBy['field'] = self.db.protectIdentifiers(orderBy['field'])
                

                orderBy = orderBy['field'] + orderBy['direction']
            

            return self.QBOrderBy = "\nORDER BY " + implode(', ', self.QBOrderBy)
        

        if (is_string(self.QBOrderBy)):
            return self.QBOrderBy
        

        return ''
    

    """
     * Takes an object as input and converts the class variables to array key/vals
     *
     * @param object object
     *
     * @return array
    """
    def objectToArray(self, object):
        if (not is_object(object)):
            return object
        

        array = []

        foreach (get_object_vars(object) as key => val):
            # There are some built in keys we need to ignore for self conversion
            if (not is_object(val) && not is_array(val) && key != '_parent_name'):
                array[key] = val
            
        

        return array
    

    """
     * Takes an object as input and converts the class variables to array key/vals
     *
     * @param object object
     *
     * @return array
    """
    def batchObjectToArray(self, object):
        if (not is_object(object)):
            return object
        

        array  = []
        out    = get_object_vars(object)
        fields = array_keys(out)

        foreach (fields as val):
            # There are some built in keys we need to ignore for self conversion
            if (val != '_parent_name'):
                i = 0

                foreach (out[val] as data):
                    array[i++][val] = data
                
            
        

        return array
    

    """
     * Determines if a represents a literal value or a field name
    """
    def isLiteral(self, str): bool:
        str = str.strip()

        if (not (str)
            || ctype_digit(str)
            || (string) (float) str == str
            || in_array(strtoupper(str), ['TRUE', 'FALSE'], True)
        ):
            return True
        

        if (self.isLiteralStr == []):
            self.isLiteralStr = self.db.escapeChar != '"' ? ['"', "'"] : ["'"]
        

        return in_array(str[0], self.isLiteralStr, True)
    

    """
     * Publicly-visible method to reset the QB values.
     *
     * @return self
    """
    def resetQuery(self, ):
        self.resetSelect()
        self.resetWrite()

        return self
    

    """
     * Resets the query builder values.  Called by the get() function
     *
     * @param array qbResetItems An array of fields to reset
    """
    def resetRun(self, array qbResetItems):
        foreach (qbResetItems as item => defaultValue)self, :
            self.{item = defaultValue
self,         
    

    """
     * Resets the query builder values.  Called by the get() function
    """
    def resetSelect(self, ):
        self.resetRun([
            'QBSelect'   => [],
            'QBJoin'     => [],
            'QBWhere'    => [],
            'QBGroupBy'  => [],
            'QBHaving'   => [],
            'QBOrderBy'  => [],
            'QBNoEscape' => [],
            'QBDistinct' => False,
            'QBLimit'    => False,
            'QBOffset'   => False,
        ])

        if (not not (self.db)):
            self.db.setAliasedTables([])
        

        # Reset QBFrom part
        if (not not (self.QBFrom)):
            self.from_(array_shift(self.QBFrom), True)
        
    

    """
     * Resets the query builder "write" values.
     *
     * Called by the insert() update() insertBatch() updateBatch() and delete() functions
    """
    def resetWrite(self, ):
        self.resetRun([
            'QBSet'     => [],
            'QBJoin'    => [],
            'QBWhere'   => [],
            'QBOrderBy' => [],
            'QBKeys'    => [],
            'QBLimit'   => False,
            'QBIgnore'  => False,
        ])
    

    """
     * Tests whether the has an SQL operator
    """
    def hasOperator(self, str): bool:
        return re.match(
            '/(<|>|!|=|\sIS None|\sIS NOT None|\sEXISTS|\sBETWEEN|\sLIKE|\sIN\s*\(|\s)/i',
            str.strip()
        ) == 1
    

    """
     * Returns the SQL operator
     *
     * @return mixed
    """
    def getOperator(self, str, list = False):
        if (self.pregOperators == []):
            _les = self.db.likeEscapeStr != ''
                ? '\s+' + re.escape(sprintf.strip()self.db.likeEscapeStr)), '/')
                : ''
            self.pregOperators = [
                '\s*(?:<|>|!)?=\s*', # =, <=, >=, !=
                '\s*<>?\s*', # <, <>
                '\s*>\s*', # >
                '\s+IS None', # IS None
                '\s+IS NOT None', # IS NOT None
                '\s+EXISTS\s*\(.*\)', # EXISTS(sql)
                '\s+NOT EXISTS\s*\(.*\)', # NOT EXISTS(sql)
                '\s+BETWEEN\s+', # BETWEEN value AND value
                '\s+IN\s*\(.*\)', # IN(list)
                '\s+NOT IN\s*\(.*\)', # NOT IN (list)
                '\s+LIKE\s+\S.*(' + _les + ')?', # LIKE 'expr'[ ESCAPE '%s']
                '\s+NOT LIKE\s+\S.*(' + _les + ')?', # NOT LIKE 'expr'[ ESCAPE '%s']
            ]
        

        return re.match_all(
            '/' + implode('|', self.pregOperators) + '/i',
            str,
            match
        ) ? (list ? match[0] : match[0][0]) : False
    

    """
     * Stores a bind value after ensuring that it's unique.
     * While it might be nicer to have named keys for our binds array
     * with PHP 7+ we get a huge memory/performance gain with indexed
     * arrays instead, so lets take advantage of that here.
     *
     * @param mixed value
    """
    def setBind(self, key, value = None, escape = True):
        if (not array_key_exists(key, self.binds)):
            self.binds[key] = [
                value,
                escape,
            ]

            return key
        

        if (not array_key_exists(key, self.bindsKeyCount)):
            self.bindsKeyCount[key] = 1
        

        len = self.bindsKeyCount[key]++

        self.binds[key + '.' + len] = [
            value,
            escape,
        ]

        return key + '.' + len
    

    """
     * Returns a clone of a Base Builder with reset query builder values.
     *
     * @return self
    """
    def cleanClone(self, ):
        return (clone self).from_([], True).resetQuery()
    

