"""*
 * This file is part of CodeIgniter 4 framework.
 *
 * (c) CodeIgniter Foundation <admin@codeigniter.com>
 *
 * For the full copyright and license information, please view
 * the LICENSE file that was distributed with this source code.
"""

Closure = object

"""*
 * Class BaseBuilder
 *
 * Provides the core Query Builder methods.
 * Database-specific Builders might need to override
 * certain methods to make them work.
"""

class BaseBuilder:

    """*
     * Reset DELETE data flag
     *
     * @var bool
     """
    resetDeleteData = False

    """*
     * QB SELECT data
     *
     * @var array
     """
    QBSelect = []

    """*
     * QB DISTINCT flag
     *
     * @var bool
     """
    QBDistinct = False

    """*
     * QB FROM data
     *
     * @var array
     """
    QBFrom = []

    """*
     * QB JOIN data
     *
     * @var array
     """
    QBJoin = []

    """*
     * QB WHERE data
     *
     * @var array
     """
    QBWhere = []

    """*
     * QB GROUP BY data
     *
     * @var array
     """
    QBGroupBy = []

    """*
     * QB HAVING data
     *
     * @var array
     """
    QBHaving = []

    """*
     * QB keys
     *
     * @var array
     """
    QBKeys = []

    """*
     * QB LIMIT data
     *
     * @var bool|int
     """
    QBLimit = False

    """*
     * QB OFFSET data
     *
     * @var bool|int
     """
    QBOffset = False

    """*
     * QB ORDER BY data
     *
     * @var array|string|null
     """
    QBOrderBy = []

    """*
     * QB NO ESCAPE data
     *
     * @var array
     """
    QBNoEscape = []

    """*
     * QB data sets
     *
     * @var array
     """
    QBSet = []

    """*
     * QB WHERE group started flag
     *
     * @var bool
     """
    QBWhereGroupStarted = False

    """*
     * QB WHERE group count
     *
     * @var int
     """
    QBWhereGroupCount = 0

    """*
     * Ignore data that cause certain
     * exceptions, for example in case of
     * duplicate keys.
     *
     * @var bool
     """
    QBIgnore = False

    """*
     * A reference to the database connection.
     *
     * @var BaseConnection
     """
    db

    """*
     * Name of the primary table for this instance.
     * Tracked separately because QBFrom gets escaped
     * and prefixed.
     *
     * @var string
     """
    tableName

    """*
     * ORDER BY random keyword
     *
     * @var array
     """
    randomKeyword = [
        'RAND()',
        'RAND(%d)',
    ]

    """*
     * COUNT string
     *
     * @used-by CI_DB_driver::count_all()
     * @used-by BaseBuilder::count_all_results()
     *
     * @var string
     """
    countString = 'SELECT COUNT(*) AS '

    """*
     * Collects the named parameters and
     * their values for later binding
     * in the Query object.
     *
     * @var array
     """
    binds = []

    """*
     * Collects the key count for named parameters
     * in the Query object.
     *
     * @var array
     """
    bindsKeyCount = []

    """*
     * Some databases, like SQLite, do not by default
     * allow limiting of delete clauses.
     *
     * @var bool
     """
    canLimitDeletes = true

    """*
     * Some databases do not by default
     * allow limit update queries with WHERE.
     *
     * @var bool
     """
    canLimitWhereUpdates = true

    """*
     * Specifies which sql statements
     * support the ignore option.
     *
     * @var array
     """
    supportedIgnoreStatements = []

    """*
     * Builder testing mode status.
     *
     * @var bool
     """
    testMode = False

    """*
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

    """*
     * Strings that determine if a string represents a literal value or a field name
     *
     * @var string[]
     """
    isLiteralStr = []

    """*
     * RegExp used to get operators
     *
     * @var string[]
     """
    pregOperators = []

    """*
     * Constructor
     *
     * @param array|string tableName
     *
     * @throws DatabaseException
     """
    def __construct(tableName, ConnectionInterface &db, ?array options = null):
        if (empty(tableName)) 
            raise DatabaseException('A table must be specified when creating a new Query Builder.')
    

        """*
         * @var BaseConnection db
         """
        this->db = db

        this->tableName = tableName
        this->from(tableName)

        if (! empty(options)) 
            foreach (options as key => value) 
                if (property_exists(this, key)) 
                    this->key} = value
            
        
    


    """*
     * Returns the current database connection
     *
     * @return BaseConnection|ConnectionInterface
     """
    def db(): ConnectionInterface:
        return this->db


    """*
     * Sets a test mode status.
     *
     * @return this
     """
    def testMode(bool mode = true):
        this->testMode = mode

        return this


    """*
     * Gets the name of the primary table.
     """
    def getTable(): string:
        return this->tableName


    """*
     * Returns an array of bind values and their
     * named parameters for binding in the Query object later.
     """
    def getBinds(): array:
        return this->binds


    """*
     * Ignore
     *
     * Set ignore Flag for next insert,
     * update or delete query.
     *
     * @return this
     """
    def ignore(bool ignore = true):
        this->QBIgnore = ignore

        return this


    """*
     * Generates the SELECT portion of the query
     *
     * @param array|string select
     *
     * @return this
     """
    def select(select = '*', ?bool escape = null):
        if (is_string(select)) 
            select = explode(',', select)
    

        // If the escape value was not set, we will base it on the global setting
        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        foreach (select as val) 
            val = trim(val)

            if (val !== '') 
                this->QBSelect[] = val

                """
                 * When doing 'SELECT NULL as field_alias FROM table'
                 * null gets taken as a field, and therefore escaped
                 * with backticks.
                 * This prevents NULL being escaped
                 * @see https://github.com/codeigniter4/CodeIgniter4/issues/1169
                 """
                if (mb_stripos(trim(val), 'NULL') === 0) 
                    escape = False
            

                this->QBNoEscape[] = escape
        
    

        return this


    """*
     * Generates a SELECT MAX(field) portion of a query
     *
     * @return this
     """
    def selectMax(string select = '', string alias = ''):
        return this->maxMinAvgSum(select, alias)


    """*
     * Generates a SELECT MIN(field) portion of a query
     *
     * @return this
     """
    def selectMin(string select = '', string alias = ''):
        return this->maxMinAvgSum(select, alias, 'MIN')


    """*
     * Generates a SELECT AVG(field) portion of a query
     *
     * @return this
     """
    def selectAvg(string select = '', string alias = ''):
        return this->maxMinAvgSum(select, alias, 'AVG')


    """*
     * Generates a SELECT SUM(field) portion of a query
     *
     * @return this
     """
    def selectSum(string select = '', string alias = ''):
        return this->maxMinAvgSum(select, alias, 'SUM')


    """*
     * Generates a SELECT COUNT(field) portion of a query
     *
     * @return this
     """
    def selectCount(string select = '', string alias = ''):
        return this->maxMinAvgSum(select, alias, 'COUNT')


    """*
     * SELECT [MAX|MIN|AVG|SUM|COUNT]()
     *
     * @used-by selectMax()
     * @used-by selectMin()
     * @used-by selectAvg()
     * @used-by selectSum()
     *
     * @throws DatabaseException
     * @throws DataException
     *
     * @return this
     """
    def maxMinAvgSum(string select = '', string alias = '', string type = 'MAX'):
        if (select === '') 
            throw DataException::forEmptyInputGiven('Select')
    

        if (strpos(select, ',') !== False) 
            throw DataException::forInvalidArgument('column name not separated by comma')
    

        type = strtoupper(type)

        if (! in_array(type, ['MAX', 'MIN', 'AVG', 'SUM', 'COUNT'], true)) 
            raise DatabaseException('Invalid def type: ' . type)
    

        if (alias === '') 
            alias = this->createAliasFromTable(trim(select))
    

        sql = type . '(' . this->db->protectIdentifiers(trim(select)) . ') AS ' . this->db->escapeIdentifiers(trim(alias))

        this->QBSelect[]   = sql
        this->QBNoEscape[] = null

        return this


    """*
     * Determines the alias name based on the table
     """
    def createAliasFromTable(string item): string:
        if (strpos(item, '.') !== False) 
            item = explode('.', item)

            return end(item)
    

        return item


    """*
     * Sets a flag which tells the query string compiler to add DISTINCT
     *
     * @return this
     """
    def distinct(bool val = true):
        this->QBDistinct = val

        return this


    """*
     * Generates the FROM portion of the query
     *
     * @param array|string from
     *
     * @return this
     """
    def from(from, bool overwrite = False):
        if (overwrite === true) 
            this->QBFrom = []
            this->db->setAliasedTables([])
    

        foreach ((array) from as val) 
            if (strpos(val, ',') !== False) 
                foreach (explode(',', val) as v) 
                    v = trim(v)
                    this->trackAliases(v)

                    this->QBFrom[] = this->db->protectIdentifiers(v, true, null, False)
            
         else 
                val = trim(val)

                // Extract any aliases that might exist. We use this information
                // in the protectIdentifiers to know whether to add a table prefix
                this->trackAliases(val)

                this->QBFrom[] = this->db->protectIdentifiers(val, true, null, False)
        
    

        return this


    """*
     * Generates the JOIN portion of the query
     *
     * @return this
     """
    def join(string table, string cond, string type = '', ?bool escape = null):
        if (type !== '') 
            type = strtoupper(trim(type))

            if (! in_array(type, this->joinTypes, true)) 
                type = ''
         else 
                type .= ' '
        
    

        // Extract any aliases that might exist. We use this information
        // in the protectIdentifiers to know whether to add a table prefix
        this->trackAliases(table)

        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        if (! this->hasOperator(cond)) 
            cond = ' USING (' . (escape ? this->db->escapeIdentifiers(cond) : cond) . ')'
     elseif (escape === False) 
            cond = ' ON ' . cond
     else 
            // Split multiple conditions
            if (preg_match_all('/\sAND\s|\sOR\s/i', cond, joints, PREG_OFFSET_CAPTURE)) 
                conditions = []
                joints     = joints[0]
                array_unshift(joints, ['', 0])

                for (i = count(joints) - 1, pos = strlen(cond) i >= 0 i--) 
                    joints[i][1] += strlen(joints[i][0]) // offset
                    conditions[i] = substr(cond, joints[i][1], pos - joints[i][1])
                    pos            = joints[i][1] - strlen(joints[i][0])
                    joints[i]     = joints[i][0]
            
                ksort(conditions)
         else 
                conditions = [cond]
                joints     = ['']
        

            cond = ' ON '

            foreach (conditions as i => condition) 
                operator = this->getOperator(condition)

                cond .= joints[i]
                cond .= preg_match('/(\(*)?([\[\]\w\.\'-]+)' . preg_quote(operator, '/') . '(.*)/i', condition, match) ? match[1] . this->db->protectIdentifiers(match[2]) . operator . this->db->protectIdentifiers(match[3]) : condition
        
    

        // Do we want to escape the table name?
        if (escape === true) 
            table = this->db->protectIdentifiers(table, true, null, False)
    

        // Assemble the JOIN statement
        this->QBJoin[] = type . 'JOIN ' . table . cond

        return this


    """*
     * Generates the WHERE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed key
     * @param mixed value
     *
     * @return this
     """
    def where(key, value = null, ?bool escape = null):
        return this->whereHaving('QBWhere', key, value, 'AND ', escape)


    """*
     * OR WHERE
     *
     * Generates the WHERE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed key
     * @param mixed value
     * @param bool  escape
     *
     * @return this
     """
    def orWhere(key, value = null, ?bool escape = null):
        return this->whereHaving('QBWhere', key, value, 'OR ', escape)


    """*
     * @used-by where()
     * @used-by orWhere()
     * @used-by having()
     * @used-by orHaving()
     *
     * @param mixed key
     * @param mixed value
     *
     * @return this
     """
    def whereHaving(string qbKey, key, value = null, string type = 'AND ', ?bool escape = null):
        if (! is_array(key)) 
            key = [key => value]
    

        // If the escape value was not set will base it on the global setting
        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        foreach (key as k => v) 
            prefix = empty(this->qbKey}) ? this->groupGetType('') : this->groupGetType(type)

            if (v !== null) 
                op = this->getOperator(k, true)

                if (! empty(op)) 
                    k = trim(k)

                    end(op)

                    op = trim(current(op))

                    if (substr(k, -1 * strlen(op)) === op) 
                        k = rtrim(strrev(preg_replace(strrev('/' . op . '/'), strrev(''), strrev(k), 1)))
                
            

                bind = this->setBind(k, v, escape)

                if (empty(op)) 
                    k .= ' ='
             else 
                    k .= " op}"
            

                if (v instanceof Closure) 
                    builder = this->cleanClone()
                    v       = '(' . str_replace("\n", ' ', v(builder)->getCompiledSelect()) . ')'
             else 
                    v = " :bind}:"
            
         elseif (! this->hasOperator(k) && qbKey !== 'QBHaving') 
                // value appears not to have been set, assign the test to IS NULL
                k .= ' IS NULL'
         elseif (preg_match('/\s*(!?=|<>|IS(?:\s+NOT)?)\s*/i', k, match, PREG_OFFSET_CAPTURE)) 
                k = substr(k, 0, match[0][1]) . (match[1][0] === '=' ? ' IS NULL' : ' IS NOT NULL')
        

            this->qbKey}[] = [
                'condition' => prefix . k . v,
                'escape'    => escape,
            ]
    

        return this


    """*
     * Generates a WHERE field IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def whereIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, False, 'AND ', escape)


    """*
     * Generates a WHERE field IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def orWhereIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, False, 'OR ', escape)


    """*
     * Generates a WHERE field NOT IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def whereNotIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, true, 'AND ', escape)


    """*
     * Generates a WHERE field NOT IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def orWhereNotIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, true, 'OR ', escape)


    """*
     * Generates a HAVING field IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def havingIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, False, 'AND ', escape, 'QBHaving')


    """*
     * Generates a HAVING field IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def orHavingIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, False, 'OR ', escape, 'QBHaving')


    """*
     * Generates a HAVING field NOT IN('item', 'item') SQL query,
     * joined with 'AND' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def havingNotIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, true, 'AND ', escape, 'QBHaving')


    """*
     * Generates a HAVING field NOT IN('item', 'item') SQL query,
     * joined with 'OR' if appropriate.
     *
     * @param array|Closure|string values The values searched on, or anonymous def with subquery
     *
     * @return this
     """
    def orHavingNotIn(?string key = null, values = null, ?bool escape = null):
        return this->_whereIn(key, values, true, 'OR ', escape, 'QBHaving')


    """*
     * @used-by WhereIn()
     * @used-by orWhereIn()
     * @used-by whereNotIn()
     * @used-by orWhereNotIn()
     *
     * @param array|Closure|null values The values searched on, or anonymous def with subquery
     *
     * @throws InvalidArgumentException
     *
     * @return this
     """
    def _whereIn(?string key = null, values = null, bool not = False, string type = 'AND ', ?bool escape = null, string clause = 'QBWhere'):
        if (empty(key) || ! is_string(key)) 
            if (CI_DEBUG) 
                raise InvalidArgumentException(sprintf('%s() expects key to be a non-empty string', debug_backtrace(0, 2)[1]['def']))
        

            return this // @codeCoverageIgnore
    

        if (values === null || (! is_array(values) && ! (values instanceof Closure))) 
            if (CI_DEBUG) 
                raise InvalidArgumentException(sprintf('%s() expects values to be of type array or closure', debug_backtrace(0, 2)[1]['def']))
        

            return this // @codeCoverageIgnore
    

        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        ok = key

        if (escape === true) 
            key = this->db->protectIdentifiers(key)
    

        not = (not) ? ' NOT' : ''

        if (values instanceof Closure) 
            builder = this->cleanClone()
            ok      = str_replace("\n", ' ', values(builder)->getCompiledSelect())
     else 
            whereIn = array_values(values)
            ok      = this->setBind(ok, whereIn, escape)
    

        prefix = empty(this->clause}) ? this->groupGetType('') : this->groupGetType(type)

        whereIn = [
            'condition' => prefix . key . not . (values instanceof Closure ? " IN (ok})" : " IN :ok}:"),
            'escape'    => False,
        ]

        this->clause}[] = whereIn

        return this


    """*
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return this
     """
    def like(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'AND ', side, '', escape, insensitiveSearch)


    """*
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return this
     """
    def notLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'AND ', side, 'NOT', escape, insensitiveSearch)


    """*
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return this
     """
    def orLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'OR ', side, '', escape, insensitiveSearch)


    """*
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return this
     """
    def orNotLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'OR ', side, 'NOT', escape, insensitiveSearch)


    """*
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return this
     """
    def havingLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'AND ', side, '', escape, insensitiveSearch, 'QBHaving')


    """*
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'AND'.
     *
     * @param mixed field
     *
     * @return this
     """
    def notHavingLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'AND ', side, 'NOT', escape, insensitiveSearch, 'QBHaving')


    """*
     * Generates a %LIKE% portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return this
     """
    def orHavingLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'OR ', side, '', escape, insensitiveSearch, 'QBHaving')


    """*
     * Generates a NOT LIKE portion of the query.
     * Separates multiple calls with 'OR'.
     *
     * @param mixed field
     *
     * @return this
     """
    def orNotHavingLike(field, string match = '', string side = 'both', ?bool escape = null, bool insensitiveSearch = False):
        return this->_like(field, match, 'OR ', side, 'NOT', escape, insensitiveSearch, 'QBHaving')


    """*
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
     * @return this
     """
    def _like(field, string match = '', string type = 'AND ', string side = 'both', string not = '', ?bool escape = null, bool insensitiveSearch = False, string clause = 'QBWhere'):
        if (! is_array(field)) 
            field = [field => match]
    

        escape = is_bool(escape) ? escape : this->db->protectIdentifiers
        side   = strtolower(side)

        foreach (field as k => v) 
            if (insensitiveSearch === true) 
                v = strtolower(v)
        

            prefix = empty(this->clause}) ? this->groupGetType('') : this->groupGetType(type)

            if (side === 'none') 
                bind = this->setBind(k, v, escape)
         elseif (side === 'before') 
                bind = this->setBind(k, "%v}", escape)
         elseif (side === 'after') 
                bind = this->setBind(k, "v}%", escape)
         else 
                bind = this->setBind(k, "%v}%", escape)
        

            likeStatement = this->_like_statement(prefix, this->db->protectIdentifiers(k, False, escape), not, bind, insensitiveSearch)

            // some platforms require an escape sequence definition for LIKE wildcards
            if (escape === true && this->db->likeEscapeStr !== '') 
                likeStatement .= sprintf(this->db->likeEscapeStr, this->db->likeEscapeChar)
        

            this->clause}[] = [
                'condition' => likeStatement,
                'escape'    => escape,
            ]
    

        return this


    """*
     * Platform independent LIKE statement builder.
     """
    def _like_statement(?string prefix, string column, ?string not, string bind, bool insensitiveSearch = False): string:
        if (insensitiveSearch === true) 
            return "prefix} LOWER(column}) not} LIKE :bind}:"
    

        return "prefix} column} not} LIKE :bind}:"


    """*
     * Starts a query group.
     *
     * @return this
     """
    def groupStart():
        return this->groupStartPrepare()


    """*
     * Starts a query group, but ORs the group
     *
     * @return this
     """
    def orGroupStart():
        return this->groupStartPrepare('', 'OR ')


    """*
     * Starts a query group, but NOTs the group
     *
     * @return this
     """
    def notGroupStart():
        return this->groupStartPrepare('NOT ')


    """*
     * Starts a query group, but OR NOTs the group
     *
     * @return this
     """
    def orNotGroupStart():
        return this->groupStartPrepare('NOT ', 'OR ')


    """*
     * Ends a query group
     *
     * @return this
     """
    def groupEnd():
        return this->groupEndPrepare()


    """*
     * Starts a query group for HAVING clause.
     *
     * @return this
     """
    def havingGroupStart():
        return this->groupStartPrepare('', 'AND ', 'QBHaving')


    """*
     * Starts a query group for HAVING clause, but ORs the group.
     *
     * @return this
     """
    def orHavingGroupStart():
        return this->groupStartPrepare('', 'OR ', 'QBHaving')


    """*
     * Starts a query group for HAVING clause, but NOTs the group.
     *
     * @return this
     """
    def notHavingGroupStart():
        return this->groupStartPrepare('NOT ', 'AND ', 'QBHaving')


    """*
     * Starts a query group for HAVING clause, but OR NOTs the group.
     *
     * @return this
     """
    def orNotHavingGroupStart():
        return this->groupStartPrepare('NOT ', 'OR ', 'QBHaving')


    """*
     * Ends a query group for HAVING clause.
     *
     * @return this
     """
    def havingGroupEnd():
        return this->groupEndPrepare('QBHaving')


    """*
     * Prepate a query group start.
     *
     * @return this
     """
    def groupStartPrepare(string not = '', string type = 'AND ', string clause = 'QBWhere'):
        type = this->groupGetType(type)

        this->QBWhereGroupStarted = true
        prefix                    = empty(this->clause}) ? '' : type
        where                     = [
            'condition' => prefix . not . str_repeat(' ', ++this->QBWhereGroupCount) . ' (',
            'escape'    => False,
        ]

        this->clause}[] = where

        return this


    """*
     * Prepate a query group end.
     *
     * @return this
     """
    def groupEndPrepare(string clause = 'QBWhere'):
        this->QBWhereGroupStarted = False
        where                     = [
            'condition' => str_repeat(' ', this->QBWhereGroupCount--) . ')',
            'escape'    => False,
        ]

        this->clause}[] = where

        return this


    """*
     * @used-by groupStart()
     * @used-by _like()
     * @used-by whereHaving()
     * @used-by _whereIn()
     * @used-by havingGroupStart()
     """
    def groupGetType(string type): string:
        if (this->QBWhereGroupStarted) 
            type                      = ''
            this->QBWhereGroupStarted = False
    

        return type


    """*
     * @param array|string by
     *
     * @return this
     """
    def groupBy(by, ?bool escape = null):
        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        if (is_string(by)) 
            by = (escape === true) ? explode(',', by) : [by]
    

        foreach (by as val) 
            val = trim(val)

            if (val !== '') 
                val = [
                    'field'  => val,
                    'escape' => escape,
                ]

                this->QBGroupBy[] = val
        
    

        return this


    """*
     * Separates multiple calls with 'AND'.
     *
     * @param array|string key
     * @param mixed        value
     *
     * @return this
     """
    def having(key, value = null, ?bool escape = null):
        return this->whereHaving('QBHaving', key, value, 'AND ', escape)


    """*
     * Separates multiple calls with 'OR'.
     *
     * @param array|string key
     * @param mixed        value
     *
     * @return this
     """
    def orHaving(key, value = null, ?bool escape = null):
        return this->whereHaving('QBHaving', key, value, 'OR ', escape)


    """*
     * @param string direction ASC, DESC or RANDOM
     *
     * @return this
     """
    def orderBy(string orderBy, string direction = '', ?bool escape = null):
        if (empty(orderBy)) 
            return this
    

        direction = strtoupper(trim(direction))

        if (direction === 'RANDOM') 
            direction = ''
            orderBy   = ctype_digit(orderBy) ? sprintf(this->randomKeyword[1], orderBy) : this->randomKeyword[0]
            escape    = False
     elseif (direction !== '') 
            direction = in_array(direction, ['ASC', 'DESC'], true) ? ' ' . direction : ''
    

        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        if (escape === False) 
            qbOrderBy[] = [
                'field'     => orderBy,
                'direction' => direction,
                'escape'    => False,
            ]
     else 
            qbOrderBy = []

            foreach (explode(',', orderBy) as field) 
                qbOrderBy[] = (direction === '' && preg_match('/\s+(ASC|DESC)/i', rtrim(field), match, PREG_OFFSET_CAPTURE))
                    ? [
                        'field'     => ltrim(substr(field, 0, match[0][1])),
                        'direction' => ' ' . match[1][0],
                        'escape'    => true,
                    ]
                    : [
                        'field'     => trim(field),
                        'direction' => direction,
                        'escape'    => true,
                    ]
        
    

        this->QBOrderBy = array_merge(this->QBOrderBy, qbOrderBy)

        return this


    """*
     * @return this
     """
    def limit(?int value = null, ?int offset = 0):
        if (value !== null) 
            this->QBLimit = value
    

        if (! empty(offset)) 
            this->QBOffset = offset
    

        return this


    """*
     * Sets the OFFSET value
     *
     * @return this
     """
    def offset(int offset):
        if (! empty(offset)) 
            this->QBOffset = (int) offset
    

        return this


    """*
     * Generates a platform-specific LIMIT clause.
     """
    def _limit(string sql, bool offsetIgnore = False): string:
        return sql . ' LIMIT ' . (offsetIgnore === False && this->QBOffset ? this->QBOffset . ', ' : '') . this->QBLimit


    """*
     * Allows key/value pairs to be set for insert(), update() or replace().
     *
     * @param array|object|string key    Field name, or an array of field/value pairs
     * @param mixed               value  Field value, if key is a single field
     * @param bool|null           escape Whether to escape values
     *
     * @return this
     """
    def set(key, value = '', ?bool escape = null):
        key = this->objectToArray(key)

        if (! is_array(key)) 
            key = [key => value]
    

        escape = is_bool(escape) ? escape : this->db->protectIdentifiers

        foreach (key as k => v) 
            if (escape) 
                bind = this->setBind(k, v, escape)

                this->QBSet[this->db->protectIdentifiers(k, False)] = ":bind}:"
         else 
                this->QBSet[this->db->protectIdentifiers(k, False)] = v
        
    

        return this


    """*
     * Returns the previously set() data, alternatively resetting it if needed.
     """
    def getSetData(bool clean = False): array:
        data = this->QBSet

        if (clean) 
            this->QBSet = []
    

        return data


    """*
     * Compiles a SELECT query string and returns the sql.
     """
    def getCompiledSelect(bool reset = true): string:
        select = this->compileSelect()

        if (reset === true) 
            this->resetSelect()
    

        return this->compileFinalQuery(select)


    """*
     * Returns a finalized, compiled query string with the bindings
     * inserted and prefixes swapped out.
     """
    def compileFinalQuery(string sql): string:
        query = new Query(this->db)
        query->setQuery(sql, this->binds, False)

        if (! empty(this->db->swapPre) && ! empty(this->db->DBPrefix)) 
            query->swapPrefix(this->db->DBPrefix, this->db->swapPre)
    

        return query->getQuery()


    """*
     * Compiles the select statement based on the other defs called
     * and runs the query
     *
     * @return False|ResultInterface
     """
    def get(?int limit = null, int offset = 0, bool reset = true):
        if (limit !== null) 
            this->limit(limit, offset)
    

        result = this->testMode
            ? this->getCompiledSelect(reset)
            : this->db->query(this->compileSelect(), this->binds, False)

        if (reset === true) 
            this->resetSelect()

            // Clear our binds so we don't eat up memory
            this->binds = []
    

        return result


    """*
     * Generates a platform-specific query string that counts all records in
     * the particular table
     *
     * @return int|string
     """
    def countAll(bool reset = true):
        table = this->QBFrom[0]

        sql = this->countString . this->db->escapeIdentifiers('numrows') . ' FROM ' .
            this->db->protectIdentifiers(table, true, null, False)

        if (this->testMode) 
            return sql
    

        query = this->db->query(sql, null, False)

        if (empty(query->getResult())) 
            return 0
    

        query = query->getRow()

        if (reset === true) 
            this->resetSelect()
    

        return (int) query->numrows


    """*
     * Generates a platform-specific query string that counts all records
     * returned by an Query Builder query.
     *
     * @return int|string
     """
    def countAllResults(bool reset = true):
        // ORDER BY usage is often problematic here (most notably
        // on Microsoft SQL Server) and ultimately unnecessary
        // for selecting COUNT(*) ...
        orderBy = []

        if (! empty(this->QBOrderBy)) 
            orderBy = this->QBOrderBy

            this->QBOrderBy = null
    

        // We cannot use a LIMIT when getting the single row COUNT(*) result
        limit = this->QBLimit

        this->QBLimit = False

        if (this->QBDistinct === true || ! empty(this->QBGroupBy)) 
            // We need to backup the original SELECT in case DBPrefix is used
            select = this->QBSelect
            sql    = this->countString . this->db->protectIdentifiers('numrows') . "\nFROM (\n" . this->compileSelect() . "\n) CI_count_all_results"

            // Restore SELECT part
            this->QBSelect = select
            unset(select)
     else 
            sql = this->compileSelect(this->countString . this->db->protectIdentifiers('numrows'))
    

        if (this->testMode) 
            return sql
    

        result = this->db->query(sql, this->binds, False)

        if (reset === true) 
            this->resetSelect()
     elseif (! isset(this->QBOrderBy)) 
            this->QBOrderBy = orderBy
    

        // Restore the LIMIT setting
        this->QBLimit = limit

        row = ! result instanceof ResultInterface ? null : result->getRow()

        if (empty(row)) 
            return 0
    

        return (int) row->numrows


    """*
     * Compiles the set conditions and returns the sql statement
     *
     * @return array
     """
    def getCompiledQBWhere():
        return this->QBWhere


    """*
     * Allows the where clause, limit and offset to be added directly
     *
     * @param array|string where
     *
     * @return ResultInterface
     """
    def getWhere(where = null, ?int limit = null, ?int offset = 0, bool reset = true):
        if (where !== null) 
            this->where(where)
    

        if (! empty(limit)) 
            this->limit(limit, offset)
    

        result = this->testMode
            ? this->getCompiledSelect(reset)
            : this->db->query(this->compileSelect(), this->binds, False)

        if (reset === true) 
            this->resetSelect()

            // Clear our binds so we don't eat up memory
            this->binds = []
    

        return result


    """*
     * Compiles batch insert strings and runs the queries
     *
     * @throws DatabaseException
     *
     * @return False|int|string[] Number of rows inserted or FALSE on failure, SQL array when testMode
     """
    def insertBatch(?array set = null, ?bool escape = null, int batchSize = 100):
        if (set === null) 
            if (empty(this->QBSet)) 
                if (CI_DEBUG) 
                    raise DatabaseException('You must use the "set" method to update an entry.')
            

                return False // @codeCoverageIgnore
        
     elseif (empty(set)) 
            if (CI_DEBUG) 
                raise DatabaseException('insertBatch() called with no data')
        

            return False // @codeCoverageIgnore
    

        hasQBSet = set === null

        table = this->QBFrom[0]

        affectedRows = 0
        savedSQL     = []

        if (hasQBSet) 
            set = this->QBSet
    

        for (i = 0, total = count(set) i < total i += batchSize) 
            if (hasQBSet) 
                QBSet = array_slice(this->QBSet, i, batchSize)
         else 
                this->setInsertBatch(array_slice(set, i, batchSize), '', escape)
                QBSet = this->QBSet
        
            sql = this->_insertBatch(this->db->protectIdentifiers(table, true, null, False), this->QBKeys, QBSet)

            if (this->testMode) 
                savedSQL[] = sql
         else 
                this->db->query(sql, null, False)
                affectedRows += this->db->affectedRows()
        

            if (! hasQBSet) 
                this->resetWrite()
        
    

        this->resetWrite()

        return this->testMode ? savedSQL : affectedRows


    """*
     * Generates a platform-specific insert string from the supplied data.
     """
    def _insertBatch(string table, array keys, array values): string:
        return 'INSERT ' . this->compileIgnore('insert') . 'INTO ' . table . ' (' . implode(', ', keys) . ') VALUES ' . implode(', ', values)


    """*
     * Allows key/value pairs to be set for batch inserts
     *
     * @param mixed key
     *
     * @return this|null
     """
    def setInsertBatch(key, string value = '', ?bool escape = null):
        key = this->batchObjectToArray(key)

        if (! is_array(key)) 
            key = [key => value]
    

        escape = is_bool(escape) ? escape : this->db->protectIdentifiers

        keys = array_keys(this->objectToArray(current(key)))
        sort(keys)

        foreach (key as row) 
            row = this->objectToArray(row)
            if (array_diff(keys, array_keys(row)) !== [] || array_diff(array_keys(row), keys) !== []) 
                // batch def above returns an error on an empty array
                this->QBSet[] = []

                return null
        

            ksort(row) // puts row in the same order as our keys

            clean = []

            foreach (row as rowValue) 
                clean[] = escape ? this->db->escape(rowValue) : rowValue
        

            row = clean

            this->QBSet[] = '(' . implode(',', row) . ')'
    

        foreach (keys as k) 
            this->QBKeys[] = this->db->protectIdentifiers(k, False)
    

        return this


    """*
     * Compiles an insert query and returns the sql
     *
     * @throws DatabaseException
     *
     * @return bool|string
     """
    def getCompiledInsert(bool reset = true):
        if (this->validateInsert() === False) 
            return False
    

        sql = this->_insert(
            this->db->protectIdentifiers(this->QBFrom[0], true, null, False),
            array_keys(this->QBSet),
            array_values(this->QBSet)
        )

        if (reset === true) 
            this->resetWrite()
    

        return this->compileFinalQuery(sql)


    """*
     * Compiles an insert string and runs the query
     *
     * @throws DatabaseException
     *
     * @return bool|Query
     """
    def insert(?array set = null, ?bool escape = null):
        if (set !== null) 
            this->set(set, '', escape)
    

        if (this->validateInsert() === False) 
            return False
    

        sql = this->_insert(
            this->db->protectIdentifiers(this->QBFrom[0], true, escape, False),
            array_keys(this->QBSet),
            array_values(this->QBSet)
        )

        if (! this->testMode) 
            this->resetWrite()

            result = this->db->query(sql, this->binds, False)

            // Clear our binds so we don't eat up memory
            this->binds = []

            return result
    

        return False


    """*
     * This method is used by both insert() and getCompiledInsert() to
     * validate that the there data is actually being set and that table
     * has been chosen to be inserted into.
     *
     * @throws DatabaseException
     """
    def validateInsert(): bool:
        if (empty(this->QBSet)) 
            if (CI_DEBUG) 
                raise DatabaseException('You must use the "set" method to update an entry.')
        

            return False // @codeCoverageIgnore
    

        return true


    """*
     * Generates a platform-specific insert string from the supplied data
     """
    def _insert(string table, array keys, array unescapedKeys): string:
        return 'INSERT ' . this->compileIgnore('insert') . 'INTO ' . table . ' (' . implode(', ', keys) . ') VALUES (' . implode(', ', unescapedKeys) . ')'


    """*
     * Compiles an replace into string and runs the query
     *
     * @throws DatabaseException
     *
     * @return BaseResult|False|Query|string
     """
    def replace(?array set = null):
        if (set !== null) 
            this->set(set)
    

        if (empty(this->QBSet)) 
            if (CI_DEBUG) 
                raise DatabaseException('You must use the "set" method to update an entry.')
        

            return False // @codeCoverageIgnore
    

        table = this->QBFrom[0]

        sql = this->_replace(table, array_keys(this->QBSet), array_values(this->QBSet))

        this->resetWrite()

        return this->testMode ? sql : this->db->query(sql, this->binds, False)


    """*
     * Generates a platform-specific replace string from the supplied data
     """
    def _replace(string table, array keys, array values): string:
        return 'REPLACE INTO ' . table . ' (' . implode(', ', keys) . ') VALUES (' . implode(', ', values) . ')'


    """*
     * Groups tables in FROM clauses if needed, so there is no confusion
     * about operator precedence.
     *
     * Note: This is only used (and overridden) by MySQL and SQLSRV.
     """
    def _fromTables(): string:
        return implode(', ', this->QBFrom)


    """*
     * Compiles an update query and returns the sql
     *
     * @return bool|string
     """
    def getCompiledUpdate(bool reset = true):
        if (this->validateUpdate() === False) 
            return False
    

        sql = this->_update(this->QBFrom[0], this->QBSet)

        if (reset === true) 
            this->resetWrite()
    

        return this->compileFinalQuery(sql)


    """*
     * Compiles an update string and runs the query.
     *
     * @param mixed where
     *
     * @throws DatabaseException
     """
    def update(?array set = null, where = null, ?int limit = null): bool:
        if (set !== null) 
            this->set(set)
    

        if (this->validateUpdate() === False) 
            return False
    

        if (where !== null) 
            this->where(where)
    

        if (! empty(limit)) 
            if (! this->canLimitWhereUpdates) 
                raise DatabaseException('This driver does not allow LIMITs on UPDATE queries using WHERE.')
        

            this->limit(limit)
    

        sql = this->_update(this->QBFrom[0], this->QBSet)

        if (! this->testMode) 
            this->resetWrite()

            result = this->db->query(sql, this->binds, False)

            if (result !== False) 
                // Clear our binds so we don't eat up memory
                this->binds = []

                return true
        

            return False
    

        return true


    """*
     * Generates a platform-specific update string from the supplied data
     """
    def _update(string table, array values): string:
        valStr = []

        foreach (values as key => val) 
            valStr[] = key . ' = ' . val
    

        return 'UPDATE ' . this->compileIgnore('update') . table . ' SET ' . implode(', ', valStr)
            . this->compileWhereHaving('QBWhere')
            . this->compileOrderBy()
            . (this->QBLimit ? this->_limit(' ', true) : '')


    """*
     * This method is used by both update() and getCompiledUpdate() to
     * validate that data is actually being set and that a table has been
     * chosen to be update.
     *
     * @throws DatabaseException
     """
    def validateUpdate(): bool:
        if (empty(this->QBSet)) 
            if (CI_DEBUG) 
                raise DatabaseException('You must use the "set" method to update an entry.')
        

            return False // @codeCoverageIgnore
    

        return true


    """*
     * Compiles an update string and runs the query
     *
     * @throws DatabaseException
     *
     * @return False|int|string[] Number of rows affected or FALSE on failure, SQL array when testMode
     """
    def updateBatch(?array set = null, ?string index = null, int batchSize = 100):
        if (index === null) 
            if (CI_DEBUG) 
                raise DatabaseException('You must specify an index to match on for batch updates.')
        

            return False // @codeCoverageIgnore
    

        if (set === null) 
            if (empty(this->QBSet)) 
                if (CI_DEBUG) 
                    raise DatabaseException('You must use the "set" method to update an entry.')
            

                return False // @codeCoverageIgnore
        
     elseif (empty(set)) 
            if (CI_DEBUG) 
                raise DatabaseException('updateBatch() called with no data')
        

            return False // @codeCoverageIgnore
    

        hasQBSet = set === null

        table = this->QBFrom[0]

        affectedRows = 0
        savedSQL     = []
        savedQBWhere = this->QBWhere

        if (hasQBSet) 
            set = this->QBSet
    

        for (i = 0, total = count(set) i < total i += batchSize) 
            if (hasQBSet) 
                QBSet = array_slice(this->QBSet, i, batchSize)
         else 
                this->setUpdateBatch(array_slice(set, i, batchSize), index)
                QBSet = this->QBSet
        

            sql = this->_updateBatch(
                table,
                QBSet,
                this->db->protectIdentifiers(index)
            )

            if (this->testMode) 
                savedSQL[] = sql
         else 
                this->db->query(sql, this->binds, False)
                affectedRows += this->db->affectedRows()
        

            if (! hasQBSet) 
                this->resetWrite()
        

            this->QBWhere = savedQBWhere
    

        this->resetWrite()

        return this->testMode ? savedSQL : affectedRows


    """*
     * Generates a platform-specific batch update string from the supplied data
     """
    def _updateBatch(string table, array values, string index): string:
        ids   = []
        final = []

        foreach (values as val) 
            ids[] = val[index]

            foreach (array_keys(val) as field) 
                if (field !== index) 
                    final[field][] = 'WHEN ' . index . ' = ' . val[index] . ' THEN ' . val[field]
            
        
    

        cases = ''

        foreach (final as k => v) 
            cases .= k . " = CASE \n"
                . implode("\n", v) . "\n"
                . 'ELSE ' . k . ' END, '
    

        this->where(index . ' IN(' . implode(',', ids) . ')', null, False)

        return 'UPDATE ' . this->compileIgnore('update') . table . ' SET ' . substr(cases, 0, -2) . this->compileWhereHaving('QBWhere')


    """*
     * Allows key/value pairs to be set for batch updating
     *
     * @param array|object key
     *
     * @throws DatabaseException
     *
     * @return this|null
     """
    def setUpdateBatch(key, string index = '', ?bool escape = null):
        key = this->batchObjectToArray(key)

        if (! is_array(key)) 
            return null
    

        if (! is_bool(escape)) 
            escape = this->db->protectIdentifiers
    

        foreach (key as v) 
            indexSet = False
            clean    = []

            foreach (v as k2 => v2) 
                if (k2 === index) 
                    indexSet = true
            

                clean[this->db->protectIdentifiers(k2, False)]
                    = escape ? this->db->escape(v2) : v2
        

            if (indexSet === False) 
                raise DatabaseException('One or more rows submitted for batch updating is missing the specified index.')
        

            this->QBSet[] = clean
    

        return this


    """*
     * Compiles a delete string and runs "DELETE FROM table"
     *
     * @return bool|string TRUE on success, FALSE on failure, string on testMode
     """
    def emptyTable():
        table = this->QBFrom[0]

        sql = this->_delete(table)

        if (this->testMode) 
            return sql
    

        this->resetWrite()

        return this->db->query(sql, null, False)


    """*
     * Compiles a truncate string and runs the query
     * If the database does not support the truncate() command
     * This def maps to "DELETE FROM table"
     *
     * @return bool|string TRUE on success, FALSE on failure, string on testMode
     """
    def truncate():
        table = this->QBFrom[0]

        sql = this->_truncate(table)

        if (this->testMode) 
            return sql
    

        this->resetWrite()

        return this->db->query(sql, null, False)


    """*
     * Generates a platform-specific truncate string from the supplied data
     *
     * If the database does not support the truncate() command,
     * then this method maps to 'DELETE FROM table'
     """
    def _truncate(string table): string:
        return 'TRUNCATE ' . table


    """*
     * Compiles a delete query string and returns the sql
     """
    def getCompiledDelete(bool reset = true): string:
        sql = this->testMode()->delete('', null, reset)
        this->testMode(False)

        return this->compileFinalQuery(sql)


    """*
     * Compiles a delete string and runs the query
     *
     * @param mixed where
     *
     * @throws DatabaseException
     *
     * @return bool|string
     """
    def delete(where = '', ?int limit = null, bool resetData = true):
        table = this->db->protectIdentifiers(this->QBFrom[0], true, null, False)

        if (where !== '') 
            this->where(where)
    

        if (empty(this->QBWhere)) 
            if (CI_DEBUG) 
                raise DatabaseException('Deletes are not allowed unless they contain a "where" or "like" clause.')
        

            return False // @codeCoverageIgnore
    

        sql = this->_delete(table)

        if (! empty(limit)) 
            this->QBLimit = limit
    

        if (! empty(this->QBLimit)) 
            if (! this->canLimitDeletes) 
                raise DatabaseException('SQLite3 does not allow LIMITs on DELETE queries.')
        

            sql = this->_limit(sql, true)
    

        if (resetData) 
            this->resetWrite()
    

        return this->testMode ? sql : this->db->query(sql, this->binds, False)


    """*
     * Increments a numeric column by the specified value.
     *
     * @return bool
     """
    def increment(string column, int value = 1):
        column = this->db->protectIdentifiers(column)

        sql = this->_update(this->QBFrom[0], [column => "column} + value}"])

        return this->db->query(sql, this->binds, False)


    """*
     * Decrements a numeric column by the specified value.
     *
     * @return bool
     """
    def decrement(string column, int value = 1):
        column = this->db->protectIdentifiers(column)

        sql = this->_update(this->QBFrom[0], [column => "column}-value}"])

        return this->db->query(sql, this->binds, False)


    """*
     * Generates a platform-specific delete string from the supplied data
     """
    def _delete(string table): string:
        return 'DELETE ' . this->compileIgnore('delete') . 'FROM ' . table . this->compileWhereHaving('QBWhere')


    """*
     * Used to track SQL statements written with aliased tables.
     *
     * @param array|string table The table to inspect
     *
     * @return string|void
     """
    def trackAliases(table):
        if (is_array(table)) 
            foreach (table as t) 
                this->trackAliases(t)
        

            return
    

        // Does the string contain a comma?  If so, we need to separate
        // the string into discreet statements
        if (strpos(table, ',') !== False) 
            return this->trackAliases(explode(',', table))
    

        // if a table alias is used we can recognize it by a space
        if (strpos(table, ' ') !== False) 
            // if the alias is written with the AS keyword, remove it
            table = preg_replace('/\s+AS\s+/i', ' ', table)

            // Grab the alias
            table = trim(strrchr(table, ' '))

            // Store the alias, if it doesn't already exist
            this->db->addTableAlias(table)
    


    """*
     * Compile the SELECT statement
     *
     * Generates a query string based on which defs were used.
     * Should not be called directly.
     *
     * @param mixed selectOverride
     """
    def compileSelect(selectOverride = False): string:
        if (selectOverride !== False) 
            sql = selectOverride
     else 
            sql = (! this->QBDistinct) ? 'SELECT ' : 'SELECT DISTINCT '

            if (empty(this->QBSelect)) 
                sql .= '*'
         else 
                // Cycle through the "select" portion of the query and prep each column name.
                // The reason we protect identifiers here rather than in the select() def
                // is because until the user calls the from() def we don't know if there are aliases
                foreach (this->QBSelect as key => val) 
                    noEscape             = this->QBNoEscape[key] ?? null
                    this->QBSelect[key] = this->db->protectIdentifiers(val, False, noEscape)
            

                sql .= implode(', ', this->QBSelect)
        
    

        if (! empty(this->QBFrom)) 
            sql .= "\nFROM " . this->_fromTables()
    

        if (! empty(this->QBJoin)) 
            sql .= "\n" . implode("\n", this->QBJoin)
    

        sql .= this->compileWhereHaving('QBWhere')
            . this->compileGroupBy()
            . this->compileWhereHaving('QBHaving')
            . this->compileOrderBy()

        if (this->QBLimit) 
            return this->_limit(sql . "\n")
    

        return sql


    """*
     * Checks if the ignore option is supported by
     * the Database Driver for the specific statement.
     *
     * @return string
     """
    def compileIgnore(string statement):
        if (this->QBIgnore && isset(this->supportedIgnoreStatements[statement])) 
            return trim(this->supportedIgnoreStatements[statement]) . ' '
    

        return ''


    """*
     * Escapes identifiers in WHERE and HAVING statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * where(), orWhere(), having(), orHaving are called prior to from(),
     * join() and prefixTable is added only if needed.
     *
     * @param string qbKey 'QBWhere' or 'QBHaving'
     *
     * @return string SQL statement
     """
    def compileWhereHaving(string qbKey): string:
        if (! empty(this->qbKey})) 
            foreach (this->qbKey} as &qbkey) 
                // Is this condition already compiled?
                if (is_string(qbkey)) 
                    continue
            

                if (qbkey['escape'] === False) 
                    qbkey = qbkey['condition']

                    continue
            

                // Split multiple conditions
                conditions = preg_split(
                    '/((?:^|\s+)AND\s+|(?:^|\s+)OR\s+)/i',
                    qbkey['condition'],
                    -1,
                    PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_EMPTY
                )

                foreach (conditions as &condition) 
                    if ((op = this->getOperator(condition)) === False
                        || ! preg_match('/^(\(?)(.*)(' . preg_quote(op, '/') . ')\s*(.*(?<!\)))?(\)?)/i', condition, matches)
                    ) 
                        continue
                
                    // matches = array(
                    //	0 => '(test <= foo)',	""" the whole thing """
                    //	1 => '(',		""" optional """
                    //	2 => 'test',		""" the field name """
                    //	3 => ' <= ',		""" op """
                    //	4 => 'foo',		""" optional, if op is e.g. 'IS NULL' """
                    //	5 => ')'		""" optional """
                    // )

                    if (! empty(matches[4])) 
                        protectIdentifiers = False
                        if (strpos(matches[4], '.') !== False) 
                            protectIdentifiers = true
                    

                        if (strpos(matches[4], ':') === False) 
                            matches[4] = this->db->protectIdentifiers(trim(matches[4]), False, protectIdentifiers)
                    

                        matches[4] = ' ' . matches[4]
                

                    condition = matches[1] . this->db->protectIdentifiers(trim(matches[2]))
                        . ' ' . trim(matches[3]) . matches[4] . matches[5]
            

                qbkey = implode('', conditions)
        

            return (qbKey === 'QBHaving' ? "\nHAVING " : "\nWHERE ")
                . implode("\n", this->qbKey})
    

        return ''


    """*
     * Escapes identifiers in GROUP BY statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * groupBy() is called prior to from(), join() and prefixTable is added
     * only if needed.
     """
    def compileGroupBy(): string:
        if (! empty(this->QBGroupBy)) 
            foreach (this->QBGroupBy as &groupBy) 
                // Is it already compiled?
                if (is_string(groupBy)) 
                    continue
            

                groupBy = (groupBy['escape'] === False || this->isLiteral(groupBy['field']))
                    ? groupBy['field']
                    : this->db->protectIdentifiers(groupBy['field'])
        

            return "\nGROUP BY " . implode(', ', this->QBGroupBy)
    

        return ''


    """*
     * Escapes identifiers in ORDER BY statements at execution time.
     *
     * Required so that aliases are tracked properly, regardless of whether
     * orderBy() is called prior to from(), join() and prefixTable is added
     * only if needed.
     """
    def compileOrderBy(): string:
        if (is_array(this->QBOrderBy) && ! empty(this->QBOrderBy)) 
            foreach (this->QBOrderBy as &orderBy) 
                if (orderBy['escape'] !== False && ! this->isLiteral(orderBy['field'])) 
                    orderBy['field'] = this->db->protectIdentifiers(orderBy['field'])
            

                orderBy = orderBy['field'] . orderBy['direction']
        

            return this->QBOrderBy = "\nORDER BY " . implode(', ', this->QBOrderBy)
    

        if (is_string(this->QBOrderBy)) 
            return this->QBOrderBy
    

        return ''


    """*
     * Takes an object as input and converts the class variables to array key/vals
     *
     * @param object object
     *
     * @return array
     """
    def objectToArray(object):
        if (! is_object(object)) 
            return object
    

        array = []

        foreach (get_object_vars(object) as key => val) 
            // There are some built in keys we need to ignore for this conversion
            if (! is_object(val) && ! is_array(val) && key !== '_parent_name') 
                array[key] = val
        
    

        return array


    """*
     * Takes an object as input and converts the class variables to array key/vals
     *
     * @param object object
     *
     * @return array
     """
    def batchObjectToArray(object):
        if (! is_object(object)) 
            return object
    

        array  = []
        out    = get_object_vars(object)
        fields = array_keys(out)

        foreach (fields as val) 
            // There are some built in keys we need to ignore for this conversion
            if (val !== '_parent_name') 
                i = 0

                foreach (out[val] as data) 
                    array[i++][val] = data
            
        
    

        return array


    """*
     * Determines if a string represents a literal value or a field name
     """
    def isLiteral(string str): bool:
        str = trim(str)

        if (empty(str)
            || ctype_digit(str)
            || (string) (float) str === str
            || in_array(strtoupper(str), ['TRUE', 'FALSE'], true)
        ) 
            return true
    

        if (this->isLiteralStr === []) 
            this->isLiteralStr = this->db->escapeChar !== '"' ? ['"', "'"] : ["'"]
    

        return in_array(str[0], this->isLiteralStr, true)


    """*
     * y-visible method to reset the QB values.
     *
     * @return this
     """
    def resetQuery():
        this->resetSelect()
        this->resetWrite()

        return this


    """*
     * Resets the query builder values.  Called by the get() def
     *
     * @param array qbResetItems An array of fields to reset
     """
    def resetRun(array qbResetItems):
        foreach (qbResetItems as item => defaultValue) 
            this->item} = defaultValue
    


    """*
     * Resets the query builder values.  Called by the get() def
     """
    def resetSelect():
        this->resetRun([
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

        if (! empty(this->db)) 
            this->db->setAliasedTables([])
    

        // Reset QBFrom part
        if (! empty(this->QBFrom)) 
            this->from(array_shift(this->QBFrom), true)
    


    """*
     * Resets the query builder "write" values.
     *
     * Called by the insert() update() insertBatch() updateBatch() and delete() defs
     """
    def resetWrite():
        this->resetRun([
            'QBSet'     => [],
            'QBJoin'    => [],
            'QBWhere'   => [],
            'QBOrderBy' => [],
            'QBKeys'    => [],
            'QBLimit'   => False,
            'QBIgnore'  => False,
        ])


    """*
     * Tests whether the string has an SQL operator
     """
    def hasOperator(string str): bool:
        return preg_match(
            '/(<|>|!|=|\sIS NULL|\sIS NOT NULL|\sEXISTS|\sBETWEEN|\sLIKE|\sIN\s*\(|\s)/i',
            trim(str)
        ) === 1


    """*
     * Returns the SQL string operator
     *
     * @return mixed
     """
    def getOperator(string str, bool list = False):
        if (this->pregOperators === []) 
            _les = this->db->likeEscapeStr !== ''
                ? '\s+' . preg_quote(trim(sprintf(this->db->likeEscapeStr, this->db->likeEscapeChar)), '/')
                : ''
            this->pregOperators = [
                '\s*(?:<|>|!)?=\s*', // =, <=, >=, !=
                '\s*<>?\s*', // <, <>
                '\s*>\s*', // >
                '\s+IS NULL', // IS NULL
                '\s+IS NOT NULL', // IS NOT NULL
                '\s+EXISTS\s*\(.*\)', // EXISTS(sql)
                '\s+NOT EXISTS\s*\(.*\)', // NOT EXISTS(sql)
                '\s+BETWEEN\s+', // BETWEEN value AND value
                '\s+IN\s*\(.*\)', // IN(list)
                '\s+NOT IN\s*\(.*\)', // NOT IN (list)
                '\s+LIKE\s+\S.*(' . _les . ')?', // LIKE 'expr'[ ESCAPE '%s']
                '\s+NOT LIKE\s+\S.*(' . _les . ')?', // NOT LIKE 'expr'[ ESCAPE '%s']
            ]
    

        return preg_match_all(
            '/' . implode('|', this->pregOperators) . '/i',
            str,
            match
        ) ? (list ? match[0] : match[0][0]) : False


    """*
     * Stores a bind value after ensuring that it's unique.
     * While it might be nicer to have named keys for our binds array
     * with PHP 7+ we get a huge memory/performance gain with indexed
     * arrays instead, so lets take advantage of that here.
     *
     * @param mixed value
     """
    def setBind(string key, value = null, bool escape = true): string:
        if (! array_key_exists(key, this->binds)) 
            this->binds[key] = [
                value,
                escape,
            ]

            return key
    

        if (! array_key_exists(key, this->bindsKeyCount)) 
            this->bindsKeyCount[key] = 1
    

        count = this->bindsKeyCount[key]++

        this->binds[key . '.' . count] = [
            value,
            escape,
        ]

        return key . '.' . count


    """*
     * Returns a clone of a Base Builder with reset query builder values.
     *
     * @return this
     """
    def cleanClone():
        return (clone this)->from([], true)->resetQuery()

}
