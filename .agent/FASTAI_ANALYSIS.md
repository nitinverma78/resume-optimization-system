# Advanced Fast.ai Coding Patterns - Analysis Report

## Key Findings from Fastai Codebase Review

Based on analysis of `tabular/core.py`, `data/core.py`, and `vision/core.py`

---

## 1. **Decorator-Based Extension Pattern (@patch)**

**What it does:** Extends existing classes with new methods/properties without inheritance

```python
# Add properties to PIL Image class
@patch(as_prop=True)
def n_px(x: Image.Image): return x.size[0] * x.size[1]

@patch(as_prop=True)
def aspect(x: Image.Image): return x.size[0]/x.size[1]

# Add methods
@patch
def to_thumb(self:Image.Image, h, w=None):
    if w is None: w=h
    im = self.copy()
    im.thumbnail((w,h))
    return im
```

**Benefits:**
- Extends third-party classes (PIL, DataFrame) without monkey patching
- Groups related functionality near usage
- One-line property definitions

---

## 2. **Dynamic Property Creation (properties() function)**

```python
# Create multiple properties at once
properties(Tabular, 'loc','iloc','targ','all_col_names','n_subsets','x_names','y')

# Implemented via programmatic property generation
def _add_prop(cls, nm):
    @property
    def f(o): return o[list(getattr(o,nm+'_names'))]
    @f.setter
    def fset(o, v): o[getattr(o,nm+'_names')] = v
    setattr(cls, nm+'s', f)
```

**Benefits:**
- DRY - avoid repetitive @property definitions
- Convention-based property names (e.g., `cat_names` → `cats` property)
- Reduces vertical space

---

## 3. **Class Attribute Defaults**

```python
class Tabular(CollBase, GetAttr, FilteredBase):
    "A `DataFrame` wrapper that knows which cols are cont/cat/y"
    _default,with_cont='procs',True  # Multiple defaults on one line
    
    def __init__(self, df, procs=None, cat_names=None, ...):
        # Use the defaults
```

**Benefits:**
- Defaults visible at class level
- Multiple related defaults on one line
- Easy to override in subclasses

---

## 4. **@delegates Decorator (Parameter Forwarding)**

```python
class TfmdDL(DataLoader):
    @delegates(DataLoader.__init__)
    def __init__(self, dataset, bs:int=64, shuffle:bool=False, 
                 num_workers:int=None, verbose:bool=False, **kwargs):
        # Automatically forwards remaining kwargs to parent
        super().__init__(dataset, bs=bs, shuffle=shuffle, **kwargs)
```

**Benefits:**
- Automatic parameter forwarding to parent/wrapped classes
- Avoids repeating long parameter lists
- Documentation shows inherited parameters

---

## 5. **GetAttr Mixin for Attribute Delegation**

```python
class Tabular(CollBase, GetAttr, FilteredBase):
    _default='procs'  # Default attribute to delegate to
    
    # Automatically delegates missing attributes to self.items
```

**Benefits:**
- Delegation pattern without boilerplate
- Acts like a wrapper transparently
- Reduces __getattr__ implementations

---

## 6. **One-line Helper Functions (No Blank Lines)**

```python
def cont_cat_split(df, max_card=20, dep_var=None):
    "Helper function that returns column names of cont and cat variables"
    cont_names, cat_names = [], []
    for label in df:
        if label in L(dep_var): continue
        if ((pd.api.types.is_integer_dtype(df[label].dtype) and
            df[label].unique().shape[0] > max_card) or
            pd.api.types.is_float_dtype(df[label].dtype)):
            cont_names.append(label)
        else: cat_names.append(label)
    return cont_names, cat_names
```

**Pattern:** Related utility functions have no blank lines between them

---

## 7. **Transform/Processor Base Classes**

```python
class TabularProc(InplaceTransform):
    "Base class to write a non-lazy tabular processor"
    def setup(self, items=None, train_setup=False):
        super().setup(getattr(items,'train',items), train_setup=False)
        return self(items.items if isinstance(items,Datasets) else items)
    
    @property
    def name(self): return f"{super().name} -- {getattr(self,'__stored_args__',{})}"
```

**Pattern:** Layered transformation pipeline with:
- `setup()` for initialization
- `__call__()` for application
- Composable via Pipeline

---

## 8. **Type Annotations as Documentation**

```python
@dispatch
def show_batch(
    x, # Input(s) in the batch
    y, # Target(s) in the batch
    samples, # List of (`x`, `y`) pairs of length `max_n`
    ctxs=None, # List of `ctx` objects to show data
    max_n=9, # Maximum number of `samples` to show
    **kwargs
):
```

**Benefits:**
- Inline comments explain parameter purpose
- Combined with type annotations
- Serves as both code and documentation

---

## 9. **Functional Composition**

```python
# Compose functions for decode pipeline
f = compose(f1, f, partial(getcallable(self.dataset,'decode'), full=full))

# Lambda factories for transforms
def det_zoom(zoom): return lambda x: zoom_cv(x, zoom)
def det_rotate(deg): return lambda x: rotate_cv(x, deg)
```

**Benefits:**
- Functions as first-class objects
- Currying for parameter binding
- Declarative transformation specifications

---

## 10. **Ternary and Conditional Assignment**

```python
# Inline conditionals
if not inplace: df = df.copy()
if reduce_memory: df = df_shrink(df)

# Ternary for complex logic
y_block = CategoryBlock() if not_numeric else RegressionBlock()

# next() with generator for find-first
new_t = next((r[0] for r in t if r[1]<=df[c].min() and r[2]>=df[c].max()), None)
```

---

## Recommendations for WORKING_PREFERENCES.md

### 1. **Add Decorator Patterns Section**
- Explain @patch for extending classes
- Show @delegates for parameter forwarding
- Document when to use decorators vs inheritance

### 2. **Property Creation Patterns**
- One-line @property definitions for simple getters
- Programmatic property creation for repeated patterns
- Class-level attribute defaults

### 3. **Layered Abstraction**
- Base classes for common patterns (Transform, Processor)
- Mixins for cross-cutting concerns (GetAttr, FilteredBase)
- Composition over deep inheritance

### 4. **Inline Documentation**
- Parameter comments on same line as parameter
- Docstrings that explain "what" not "how"
- Type annotations + inline comments = documentation

### 5. **Functional Programming**
- Lambda factories for parameterized transforms
- compose() for pipelines
- partial() for currying

Should I update the WORKING_PREFERENCES.md with these insights?
