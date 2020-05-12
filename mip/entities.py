from builtins import property
from typing import List, Optional, Dict, Union, Tuple
import numbers
import mip


class Column:
    """A column contains all the non-zero entries of a variable in the
    constraint matrix. To create a variable see
    :meth:`~mip.Model.add_var`."""

    __slots__ = ["constrs", "coeffs"]

    def __init__(
        self,
        constrs: Optional[List["mip.Constr"]] = None,
        coeffs: Optional[List[numbers.Real]] = None,
    ):
        self.constrs = constrs
        self.coeffs = coeffs

    def __str__(self) -> str:
        res = "["
        for k in range(len(self.constrs)):
            res += "{} {}".format(self.coeffs[k], self.constrs[k].name)
            if k < len(self.constrs) - 1:
                res += ", "
        res += "]"
        return res


class LinExpr:
    """
    Linear expressions are used to enter the objective function and the model \
    constraints. These expressions are created using operators and variables.

    Consider a model object m, the objective function of :code:`m` can be
    specified as:

    .. code:: python

     m.objective = 10*x1 + 7*x4

    In the example bellow, a constraint is added to the model

    .. code:: python

     m += xsum(3*x[i] i in range(n)) - xsum(x[i] i in range(m))

    A constraint is just a linear expression with the addition of a sense (==,
    <= or >=) and a right hand side, e.g.:

    .. code:: python

     m += x1 + x2 + x3 == 1

    If used in intermediate calculations, the solved value of the linear
    expression can be obtained with the ``x`` parameter, just as with
    a ``Var``.

    .. code:: python

     a = 10*x1 + 7*x4
     print(a.x)

    """

    __slots__ = ["__const", "__expr", "__sense"]

    def __init__(
        self,
        variables: List["mip.Var"] = [],
        coeffs: List[numbers.Real] = [],
        const: numbers.Real = 0.0,
        sense: str = "",
    ):
        self.__const = const
        self.__expr = {}  # type: Dict[mip.Var, numbers.Real]
        self.__sense = sense

        if variables:
            if len(variables) != len(coeffs):
                raise ValueError(
                    "Coefficients and variables must be same length."
                )
            for i in range(len(coeffs)):
                if abs(coeffs[i]) <= 1e-12:
                    continue
                self.add_var(variables[i], coeffs[i])

    def __add__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        result = self.copy()
        if isinstance(other, Var):
            result.add_var(other, 1)
        elif isinstance(other, LinExpr):
            result.add_expr(other)
        elif isinstance(other, numbers.Real):
            result.add_const(other)
        else:
            raise TypeError("type {} not supported".format(type(other)))
        return result

    def __radd__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        return self.__add__(other)

    def __iadd__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        if isinstance(other, Var):
            self.add_var(other, 1)
        elif isinstance(other, LinExpr):
            self.add_expr(other)
        elif isinstance(other, numbers.Real):
            self.add_const(other)
        else:
            raise TypeError("type {} not supported".format(type(other)))
        return self

    def __sub__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        result = self.copy()
        if isinstance(other, Var):
            result.add_var(other, -1)
        elif isinstance(other, LinExpr):
            result.add_expr(other, -1)
        elif isinstance(other, numbers.Real):
            result.add_const(-other)
        else:
            raise TypeError("type {} not supported".format(type(other)))
        return result

    def __rsub__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        return (-self).__add__(other)

    def __isub__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        if isinstance(other, Var):
            self.add_var(other, -1)
        elif isinstance(other, LinExpr):
            self.add_expr(other, -1)
        elif isinstance(other, numbers.Real):
            self.add_const(-other)
        else:
            raise TypeError("type {} not supported".format(type(other)))
        return self

    def __mul__(self: "LinExpr", other: numbers.Real) -> "LinExpr":
        if not isinstance(other, numbers.Real):
            raise TypeError(
                "Can not multiply with type {}".format(type(other))
            )
        result = self.copy()
        result.__const *= other
        for var in result.__expr.keys():
            result.__expr[var] *= other
        return result

    def __rmul__(self: "LinExpr", other: numbers.Real) -> "LinExpr":
        return self.__mul__(other)

    def __imul__(self: "LinExpr", other: numbers.Real) -> "LinExpr":
        if not isinstance(other, numbers.Real):
            raise TypeError(
                "Can not multiply with type {}".format(type(other))
            )
        self.__const *= other
        for var in self.__expr.keys():
            self.__expr[var] *= other
        return self

    def __truediv__(self: "LinExpr", other: numbers.Real) -> "LinExpr":
        if not isinstance(other, numbers.Real):
            raise TypeError("Can not divide with type {}".format(type(other)))
        result = self.copy()
        result.__const /= other
        for var in result.__expr.keys():
            result.__expr[var] /= other
        return result

    def __itruediv__(self: "LinExpr", other: numbers.Real) -> "LinExpr":
        if not isinstance(other, numbers.Real):
            raise TypeError("Can not divide with type {}".format(type(other)))
        self.__const /= other
        for var in self.__expr.keys():
            self.__expr[var] /= other
        return self

    def __neg__(self: "LinExpr") -> "LinExpr":
        return self.__mul__(-1)

    def __str__(self: "LinExpr") -> str:
        result = []

        if hasattr(self, "__sense"):
            if self.__sense == mip.MINIMIZE:
                result.append("Minimize ")
            elif self.__sense == mip.MAXIMIZE:
                result.append("Minimize ")

        if self.__expr:
            for var, coeff in self.__expr.items():
                result.append("+ " if coeff >= 0 else "- ")
                result.append(str(abs(coeff)) if abs(coeff) != 1 else "")
                result.append("{var} ".format(**locals()))

        if hasattr(self, "__sense"):
            if self.__sense == mip.EQUAL:
                result.append(" = ")
            if self.__sense == mip.LESS_OR_EQUAL:
                result.append(" <= ")
            if self.__sense == mip.GREATER_OR_EQUAL:
                result.append(" >= ")
            result.append(
                str(abs(self.__const))
                if self.__const < 0
                else "- " + str(abs(self.__const))
            )
        elif self.__const != 0:
            result.append(
                "+ " + str(abs(self.__const))
                if self.__const > 0
                else "- " + str(abs(self.__const))
            )

        return "".join(result)

    def __eq__(self: "LinExpr", other) -> "LinExpr":
        result = self - other
        result.__sense = "="
        return result

    def __le__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        result = self - other
        result.__sense = "<"
        return result

    def __ge__(
        self: "LinExpr", other: Union["mip.Var", "LinExpr", numbers.Real],
    ) -> "LinExpr":
        result = self - other
        result.__sense = ">"
        return result

    def add_const(self: "LinExpr", val: numbers.Real):
        """adds a constant value to the linear expression, in the case of
        a constraint this correspond to the right-hand-side

        Args:
            val(numbers.Real): a real number
        """
        self.__const += val

    def add_expr(self: "LinExpr", expr: "LinExpr", coeff: numbers.Real = 1):
        """Extends a linear expression with the contents of another.

        Args:
            expr (LinExpr): another linear expression
            coeff (numbers.Real): coefficient which will multiply the linear
                expression added
        """
        self.__const += expr.const * coeff
        for var, coeff_var in expr.expr.items():
            self.add_var(var, coeff_var * coeff)

    def add_term(
        self: "LinExpr",
        term: Union["mip.Var", "LinExpr", numbers.Real],
        coeff: numbers.Real = 1,
    ):
        """Adds a term to the linear expression.

        Args:
            expr (Union[mip.Var, LinExpr, numbers.Real]) : can be a
                variable, another linear expression or a real number.

            coeff (numbers.Real) : coefficient which will multiply the added
                term

        """
        if isinstance(term, Var):
            self.add_var(term, coeff)
        elif isinstance(term, LinExpr):
            self.add_expr(term, coeff)
        elif isinstance(term, numbers.Real):
            self.add_const(term)
        else:
            raise TypeError("type {} not supported".format(type(term)))

    def add_var(self: "LinExpr", var: "mip.Var", coeff: numbers.Real = 1):
        """Adds a variable with a coefficient to the linear expression.

        Args:
            var (mip.Var) : a variable
            coeff (numbers.Real) : coefficient which the variable will be added
        """
        if var in self.__expr:
            if -mip.EPS <= self.__expr[var] + coeff <= mip.EPS:
                del self.__expr[var]
            else:
                self.__expr[var] += coeff
        else:
            self.__expr[var] = coeff

    def copy(self: "LinExpr") -> "LinExpr":
        copy = LinExpr()
        copy.__const = self.__const
        copy.__expr = self.__expr.copy()
        copy.__sense = self.__sense
        return copy

    def equals(self: "LinExpr", other: "LinExpr") -> bool:
        """returns true if a linear expression equals to another,
        false otherwise"""
        if self.__sense != other.__sense:
            return False
        if len(self.__expr) != len(other.__expr):
            return False
        if abs(self.__const - other.__const) >= 1e-12:
            return False
        other_contents = {vr.idx: coef for vr, coef in other.__expr.items()}
        for (v, c) in self.__expr.items():
            if v.idx not in other_contents:
                return False
            oc = other_contents[v.idx]
            if abs(c - oc) > 1e-12:
                return False
        return True

    def __hash__(self: "LinExpr"):
        hash_el = [v.idx for v in self.__expr.keys()]
        for c in self.__expr.values():
            hash_el.append(c)
        hash_el.append(self.__const)
        hash_el.append(self.__sense)
        return hash(tuple(hash_el))

    @property
    def const(self: "LinExpr") -> numbers.Real:
        """constant part of the linear expression"""
        return self.__const

    @property
    def expr(self: "LinExpr") -> Dict["mip.Var", numbers.Real]:
        """the non-constant part of the linear expression

        Dictionary with pairs: (variable, coefficient) where coefficient
        is a real number.

        :rtype: Dict[mip.Var, numbers.Real]
        """
        return self.__expr

    @property
    def sense(self: "LinExpr") -> str:
        """sense of the linear expression

        sense can be EQUAL("="), LESS_OR_EQUAL("<"), GREATER_OR_EQUAL(">") or
        empty ("") if this is an affine expression, such as the objective
        function
        """
        return self.__sense

    @sense.setter
    def sense(self: "LinExpr", value):
        """sense of the linear expression

        sense can be EQUAL("="), LESS_OR_EQUAL("<"), GREATER_OR_EQUAL(">") or
        empty ("") if this is an affine expression, such as the objective
        function
        """
        self.__sense = value

    @property
    def violation(self: "LinExpr"):
        """Amount that current solution violates this constraint

        If a solution is available, than this property indicates how much
        the current solution violates this constraint.
        """
        lhs = sum(coef * var.x for (var, coef) in self.__expr.items())
        rhs = -self.const
        if self.sense == "=":
            viol = abs(lhs - rhs)
        elif self.sense == "<":
            viol = max(lhs - rhs, 0.0)
        elif self.sense == ">":
            viol = max(rhs - lhs, 0.0)
        else:
            raise ValueError("Invalid sense {}".format(self.sense))

        return viol

    @property
    def x(self) -> Optional[numbers.Real]:
        """Value of this linear expression in the solution. None
        is returned if no solution is available."""
        x = self.__const
        for var, coef in self.__expr.items():
            var_x = var.x
            if var_x is None:
                return None
            x += var_x * coef
        return x

    @property
    def model(self: "LinExpr") -> Optional["mip.Model"]:
        """Model which this LinExpr refers to, None if no variables are
        involved.

        :rtype: Optional[mip.Model]
        """
        if not self.expr:
            return None

        return self.expr.keys()[0].model


class Constr:
    """ A row (constraint) in the constraint matrix.

        A constraint is a specific :class:`~LinExpr` that includes a
        sense (<, > or == or less-or-equal, greater-or-equal and equal,
        respectively) and a right-hand-side constant value. Constraints can be
        added to the model using the overloaded operator :code:`+=` or using
        the method :meth:`~mip.Model.add_constr` of the
        :class:`~mip.model.Model` class:

        .. code:: python

          m += 3*x1 + 4*x2 <= 5

        summation expressions are also supported:

        .. code:: python

          m += xsum(x[i] for i in range(n)) == 1
    """

    __slots__ = ["__model", "idx"]

    def __init__(self, model: "mip.Model", idx: int):
        self.__model = model
        self.idx = idx

    def __hash__(self) -> int:
        return self.idx

    def __str__(self) -> str:
        if self.name:
            res = self.name + ":"
        else:
            res = "constr({}): ".format(self.idx + 1)
        line = ""
        len_line = 0
        for (var, val) in self.expr.expr.items():
            astr = " {:+} {}".format(val, var.name)
            len_line += len(astr)
            line += astr

            if len_line > 75:
                line += "\n\t"
                len_line = 0
        res += line
        rhs = self.expr.const * -1.0
        if self.expr.sense == "=":
            res += " = {}".format(rhs)
        elif self.expr.sense == "<":
            res += " <= {}".format(rhs)
        elif self.expr.sense == ">":
            res += " >= {}".format(rhs)
        else:
            raise ValueError("Invalid sense {}".format(self.expr.sense))

        return res

    @property
    def rhs(self) -> numbers.Real:
        """The right-hand-side (constant value) of the linear constraint."""
        return self.__model.solver.constr_get_rhs(self.idx)

    @rhs.setter
    def rhs(self, rhs: numbers.Real):
        self.__model.solver.constr_set_rhs(self.idx, rhs)

    @property
    def slack(self) -> Optional[numbers.Real]:
        """Value of the slack in this constraint in the optimal
        solution. Available only if the formulation was solved.
        """
        return self.__model.solver.constr_get_slack(self)

    @property
    def pi(self) -> Optional[numbers.Real]:
        """Value for the dual variable of this constraint in the optimal
        solution of a linear programming :class:`~mip.model.Model`. Only
        available if a pure linear programming problem was solved (only
        continuous variables).
        """
        return self.__model.solver.constr_get_pi(self)

    @property
    def expr(self) -> LinExpr:
        """Linear expression that defines the constraint.

        :rtype: mip.LinExpr"""
        return self.__model.solver.constr_get_expr(self)

    @expr.setter
    def expr(self, value: LinExpr):
        self.__model.solver.constr_set_expr(self, value)

    @property
    def name(self) -> str:
        """constraint name"""
        return self.__model.solver.constr_get_name(self.idx)


class Var:
    """ Decision variable of the :class:`~mip.model.Model`. The creation of
    variables is performed calling the :meth:`~mip.Model.add_var`."""

    __slots__ = ["__model", "idx"]

    def __init__(self, model: "mip.Model", idx: int):
        self.__model = model
        self.idx = idx

    def __hash__(self) -> int:
        return self.idx

    def __add__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [1, 1])
        if isinstance(other, LinExpr):
            return other.__add__(self)
        if isinstance(other, numbers.Real):
            return LinExpr([self], [1], other)

        raise TypeError("type {} not supported".format(type(other)))

    def __radd__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        return self.__add__(other)

    def __sub__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [1, -1])
        elif isinstance(other, LinExpr):
            return (-other).__iadd__(self)
        elif isinstance(other, numbers.Real):
            return LinExpr([self], [1], -other)
        else:
            raise TypeError("type {} not supported".format(type(other)))

    def __rsub__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [-1, 1])
        elif isinstance(other, LinExpr):
            return other.__sub__(self)
        elif isinstance(other, numbers.Real):
            return LinExpr([self], [-1], other)
        else:
            raise TypeError("type {} not supported".format(type(other)))

    def __mul__(self, other: numbers.Real) -> LinExpr:
        if not isinstance(other, numbers.Real):
            raise TypeError(
                "Can not multiply with type {}".format(type(other))
            )
        return LinExpr([self], [other])

    def __rmul__(self, other: numbers.Real) -> LinExpr:
        return self.__mul__(other)

    def __truediv__(self, other: numbers.Real) -> LinExpr:
        if not isinstance(other, numbers.Real):
            raise TypeError("Can not divide with type {}".format(type(other)))
        return self.__mul__(1.0 / other)

    def __neg__(self) -> LinExpr:
        return LinExpr([self], [-1.0])

    def __eq__(self, other) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [1, -1], sense="=")
        elif isinstance(other, LinExpr):
            return other == self
        elif isinstance(other, numbers.Real):
            if other != 0:
                return LinExpr([self], [1], -1 * other, sense="=")
            return LinExpr([self], [1], sense="=")
        else:
            raise TypeError("type {} not supported".format(type(other)))

    def __le__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [1, -1], sense="<")
        elif isinstance(other, LinExpr):
            return other >= self
        elif isinstance(other, numbers.Real):
            if other != 0:
                return LinExpr([self], [1], -1 * other, sense="<")
            return LinExpr([self], [1], sense="<")
        else:
            raise TypeError("type {} not supported".format(type(other)))

    def __ge__(
        self, other: Union["mip.Var", LinExpr, numbers.Real]
    ) -> LinExpr:
        if isinstance(other, Var):
            return LinExpr([self, other], [1, -1], sense=">")
        elif isinstance(other, LinExpr):
            return other <= self
        elif isinstance(other, numbers.Real):
            if other != 0:
                return LinExpr([self], [1], -1 * other, sense=">")
            return LinExpr([self], [1], sense=">")
        else:
            raise TypeError("type {} not supported".format(type(other)))

    @property
    def name(self) -> str:
        """Variable name."""
        return self.__model.solver.var_get_name(self.idx)

    def __str__(self) -> str:
        return self.name

    @property
    def lb(self) -> numbers.Real:
        """Variable lower bound."""
        return self.__model.solver.var_get_lb(self)

    @lb.setter
    def lb(self, value: numbers.Real):
        self.__model.solver.var_set_lb(self, value)

    @property
    def ub(self) -> numbers.Real:
        """Variable upper bound."""
        return self.__model.solver.var_get_ub(self)

    @ub.setter
    def ub(self, value: numbers.Real):
        self.__model.solver.var_set_ub(self, value)

    @property
    def obj(self) -> numbers.Real:
        """Coefficient of variable in the objective function."""
        return self.__model.solver.var_get_obj(self)

    @obj.setter
    def obj(self, value: numbers.Real):
        self.__model.solver.var_set_obj(self, value)

    @property
    def var_type(self) -> str:
        """Variable type: ('B') BINARY, ('C') CONTINUOUS and ('I') INTEGER."""
        return self.__model.solver.var_get_var_type(self)

    @var_type.setter
    def var_type(self, value: str):
        if value not in (mip.BINARY, mip.CONTINUOUS, mip.INTEGER):
            raise ValueError(
                "Expected one of {}, but got {}".format(
                    (mip.BINARY, mip.CONTINUOUS, mip.INTEGER), value
                )
            )
        self.__model.solver.var_set_var_type(self, value)

    @property
    def column(self) -> Column:
        """Variable coefficients in constraints.

        :rtype: mip.Column
        """
        return self.__model.solver.var_get_column(self)

    @column.setter
    def column(self, value: Column):
        self.__model.solver.var_set_column(self, value)

    @property
    def rc(self) -> Optional[numbers.Real]:
        """Reduced cost, only available after a linear programming model (only
        continuous variables) is optimized. Note that None is returned if no
        optimum solution is available"""

        return self.__model.solver.var_get_rc(self)

    @property
    def x(self) -> Optional[numbers.Real]:
        """Value of this variable in the solution. Note that None is returned
        if no solution is not available."""
        return self.__model.solver.var_get_x(self)

    def xi(self, i: int) -> Optional[numbers.Real]:
        """Value for this variable in the :math:`i`-th solution from the solution
        pool. Note that None is returned if the solution is not available."""
        if self.__model.status in [
            mip.OptimizationStatus.OPTIMAL,
            mip.OptimizationStatus.FEASIBLE,
        ]:
            return self.__model.solver.var_get_xi(self, i)
        return None

    def model(self: "mip.Var") -> "mip.Model":
        """Model which this variable refers to.

        :rtype: mip.Model
        """
        return self.__model


class ConflictGraph:

    """A conflict graph stores conflicts between incompatible assignments in
    binary variables.

    For example, if there is a constraint x1 + x2 ≤ 1 then
    there is a conflict between x1 == 1 and x2 == 1. We can state
    that x1 and x2 are conflicting. Conflicts can also involve the complement
    of a binary variable. For example, if there is a constraint x1 ≤ x2 then
    there is a conflict between x1 == 1 and x2 == 0. We now can state that x1
    and ¬x2 are conflicting."""

    __slots__ = ["model"]

    def __init__(self: "ConflictGraph", model: "mip.Model"):
        self.model = model

    def conflicting(
        self: "ConflictGraph",
        e1: Union["mip.LinExpr", "mip.Var"],
        e2: Union["mip.LinExpr", "mip.Var"],
    ) -> bool:
        """Checks if two assignments of binary variables are in conflict.

        Args:
            e1 (Union["mip.LinExpr", "mip.Var"]): binary variable, if assignment to be
            tested is the assignment to one or a linear expression like x == 0
            to indicate the complement.

            e2 (Union["mip.LinExpr", "mip.Var"]): binary variable, if assignment to be
            tested is the assignment to one or a linear expression line x == 0
            to indicate the complement.
        """
        if isinstance(e1, [LinExpr, Var]):
            raise TypeError("type {} not supported".format(type(e1)))
        if isinstance(e2, [LinExpr, Var]):
            raise TypeError("type {} not supported".format(type(e2)))

        return e1.model.solver.conflicting(e1, e2)

    def conflicting_assignments(
        self: "ConflictGraph", v1: Union["mip.LinExpr", "mip.Var"]
    ) -> Tuple[List[Var], List[Var]]:
        """Returns from the conflict graph all assignments conflicting with one
        specific assignment.

        Args:
            v1 (Var, LinExpr): binary variable, if assignment to be
            tested is the assignment to one or a linear expression like x == 0
            to indicate the complement.


        Returns:
            Returns a tuple with two lists: the first one indicates variables
            whose conflict occurs when setting them to one. The second list
            includes variable whose conflict occurs when setting them to zero.
        """
        if isinstance(v1, [LinExpr, Var]):
            raise TypeError("type {} not supported".format(type(v1)))

        return v1.model.solver.conflicting_nodes(v1)
