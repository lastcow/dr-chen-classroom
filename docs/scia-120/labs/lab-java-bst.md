---
title: "Lab — Binary Search Tree in Java"
course: SCIA-120
topic: Data Structures / Algorithms
difficulty: ⭐⭐
estimated_time: 60–75 min
---

# Lab — Binary Search Tree in Java

**Course:** SCIA-120 · Introduction to Secure Computing  
**Frostburg State University — Department of Computer Science & Information Technology**

---

## Overview

A **Binary Search Tree (BST)** is a fundamental data structure in which each node stores a value and has at most two children. The key property that makes a BST efficient is the **ordering invariant**:

> Left subtree values < Node value < Right subtree values

This ordering lets us search, insert, and delete in **O(log n)** time on average — far better than scanning a plain list. BSTs underlie databases, compilers, and many security tools (e.g., fast IP-lookup tables, certificate stores).

In this lab you will **build a complete BST from scratch in Java**, compile and run every step inside a Docker container, and observe exactly how the data structure behaves.

```
        50          ← root
       /  \
     30    70
    /  \  /  \
   20  40 60  80
```

---

## Learning Objectives

By the end of this lab you will be able to:

1. Implement a BST node class and a BST class in Java
2. Insert values and maintain the BST ordering property
3. Perform in-order, pre-order, and post-order traversals
4. Search for a value using the BST property
5. Find the minimum value and delete a node (including the tricky two-children case)
6. Run and verify Java programs inside a Docker container without installing Java on your machine

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Docker Desktop | [Download](https://www.docker.com/products/docker-desktop) — installed and running |
| Terminal | PowerShell (Windows) · Terminal (macOS/Linux) |
| A text editor | VS Code, Notepad, nano — any editor works |
| Basic Java familiarity | Variables, methods, and classes |

!!! info "No Java Installation Needed"
    Everything runs inside the `eclipse-temurin:21-jdk-alpine` Docker image.  
    Java 21 LTS is pulled automatically — nothing to install on your machine.

---

## Part 1 — Environment Setup

### Step 1.1 — Create a working directory

Open a terminal and create a folder for this lab:

```bash
mkdir bst-lab
cd bst-lab
```

### Step 1.2 — Pull the Java Docker image

```bash
docker pull eclipse-temurin:21-jdk-alpine
```

**Expected output:**
```
Status: Downloaded newer image for eclipse-temurin:21-jdk-alpine
docker.io/library/eclipse-temurin:21-jdk-alpine
```

### Step 1.3 — Verify Java is available

```bash
docker run --rm eclipse-temurin:21-jdk-alpine java --version
```

**Expected output:**
```
openjdk 21.0.10 2026-01-20 LTS
OpenJDK Runtime Environment Temurin-21.0.10+7 (build 21.0.10+7-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.10+7 (build 21.0.10+7-LTS, mixed mode, sharing)
```

📸 **Screenshot checkpoint A** — terminal showing Java version output

---

## Part 2 — The Node Class

Every BST is made of **nodes**. Each node holds:

- `data` — the integer value stored at this position
- `left` — a reference to the left child node (smaller values)
- `right` — a reference to the right child node (larger values)

### Step 2.1 — Create `Node.java`

Inside your `bst-lab` folder, create a file named **`Node.java`** with this content:

```java
public class Node {
    int data;
    Node left, right;

    public Node(int data) {
        this.data = data;
        this.left = null;
        this.right = null;
    }
}
```

**What this does:**

| Line | Meaning |
|------|---------|
| `int data` | Stores the integer value at this node |
| `Node left, right` | Pointers to child nodes (null = no child) |
| Constructor | Sets data, initializes both children to null |

### Step 2.2 — Compile Node.java via Docker

```bash
docker run --rm -v "$(pwd)":/lab -w /lab \
  eclipse-temurin:21-jdk-alpine \
  javac Node.java
```

!!! note "Windows PowerShell users"
    Replace `$(pwd)` with `${PWD}`:
    ```powershell
    docker run --rm -v "${PWD}:/lab" -w /lab eclipse-temurin:21-jdk-alpine javac Node.java
    ```

**Expected:** No output, exit code 0, and a `Node.class` file appears in the folder.

```bash
ls *.class
```
```
Node.class
```

---

## Part 3 — The BST Class: Insert & Traversals

### Step 3.1 — Create `BST.java` (Part A: Insert + Traversals)

Create **`BST.java`** with the following code:

```java
public class BST {
    Node root;

    public BST() {
        this.root = null;
    }

    // ── INSERT ────────────────────────────────────────────────────────────
    public Node insert(Node root, int data) {
        if (root == null) {
            return new Node(data);      // empty spot found → place node here
        }
        if (data < root.data) {
            root.left = insert(root.left, data);   // go left (smaller)
        } else if (data > root.data) {
            root.right = insert(root.right, data); // go right (larger)
        }
        // duplicate values are silently ignored
        return root;
    }

    // ── TRAVERSALS ────────────────────────────────────────────────────────
    // In-order: Left → Root → Right  → produces SORTED output
    public void inOrder(Node root) {
        if (root != null) {
            inOrder(root.left);
            System.out.print(root.data + " ");
            inOrder(root.right);
        }
    }

    // Pre-order: Root → Left → Right  → root always printed first
    public void preOrder(Node root) {
        if (root != null) {
            System.out.print(root.data + " ");
            preOrder(root.left);
            preOrder(root.right);
        }
    }

    // Post-order: Left → Right → Root  → root always printed last
    public void postOrder(Node root) {
        if (root != null) {
            postOrder(root.left);
            postOrder(root.right);
            System.out.print(root.data + " ");
        }
    }

    public static void main(String[] args) {
        BST tree = new BST();
        int[] values = {50, 30, 70, 20, 40, 60, 80};

        System.out.println("=== Binary Search Tree Lab ===\n");

        // Insert all values
        System.out.println("Inserting: 50, 30, 70, 20, 40, 60, 80");
        for (int v : values) {
            tree.root = tree.insert(tree.root, v);
        }
        System.out.println("Root node: " + tree.root.data);

        // Print traversals
        System.out.print("\nIn-Order   (sorted): ");
        tree.inOrder(tree.root);

        System.out.print("\nPre-Order  (root first): ");
        tree.preOrder(tree.root);

        System.out.print("\nPost-Order (root last):  ");
        tree.postOrder(tree.root);
        System.out.println();
    }
}
```

### Step 3.2 — Compile and run via Docker

```bash
docker run --rm -v "$(pwd)":/lab -w /lab \
  eclipse-temurin:21-jdk-alpine \
  sh -c "javac Node.java BST.java && java BST"
```

**Expected output:**
```
=== Binary Search Tree Lab ===

Inserting: 50, 30, 70, 20, 40, 60, 80
Root node: 50

In-Order   (sorted): 20 30 40 50 60 70 80 
Pre-Order  (root first): 50 30 20 40 70 60 80 
Post-Order (root last):  20 40 30 60 80 70 50 
```

!!! tip "Why In-Order gives sorted output"
    In-order traversal visits Left → Root → Right at every node. Because BSTs keep smaller values on the left, visiting left-first naturally produces ascending order. This is exactly how a BST can replace a sorted array for fast ordered access.

📸 **Screenshot checkpoint B** — terminal showing all three traversal outputs

---

## Part 4 — Search and Min/Max

### Step 4.1 — Add `search` and `findMin` methods

Add these two methods to `BST.java` **before** the `main` method:

```java
// ── SEARCH ────────────────────────────────────────────────────────────────
// Returns true if target exists in the tree, false otherwise
public boolean search(Node root, int target) {
    if (root == null) return false;           // fell off the tree → not found
    if (root.data == target) return true;     // found it!
    if (target < root.data)
        return search(root.left, target);     // go left (target is smaller)
    return search(root.right, target);        // go right (target is larger)
}

// ── FIND MINIMUM ──────────────────────────────────────────────────────────
// The leftmost node always holds the smallest value in a BST
public Node findMin(Node root) {
    if (root == null) return null;
    while (root.left != null) root = root.left;
    return root;
}
```

### Step 4.2 — Update `main` to test search and min

Add these lines inside `main`, **after** the traversal block:

```java
// Search
System.out.println("\n--- Search ---");
System.out.println("Search 40: " + tree.search(tree.root, 40));
System.out.println("Search 99: " + tree.search(tree.root, 99));

// Min
System.out.println("\n--- Min / Max ---");
System.out.println("Minimum: " + tree.findMin(tree.root).data);
```

### Step 4.3 — Run and verify

```bash
docker run --rm -v "$(pwd)":/lab -w /lab \
  eclipse-temurin:21-jdk-alpine \
  sh -c "javac Node.java BST.java && java BST"
```

**Expected new output (appended to Part 3 output):**
```
--- Search ---
Search 40: true
Search 99: false

--- Min / Max ---
Minimum: 20
```

!!! note "Search complexity"
    Each comparison eliminates half the remaining nodes (like binary search). In a balanced BST, search is **O(log n)**. In the worst case (a degenerate "stick" tree), it degrades to **O(n)**.

📸 **Screenshot checkpoint C** — search and minimum output

---

## Part 5 — Delete a Node

Deletion is the trickiest BST operation because there are **three cases**:

| Case | Situation | Solution |
|------|-----------|----------|
| 1 | Node has **no children** (leaf) | Simply remove it |
| 2 | Node has **one child** | Replace node with its child |
| 3 | Node has **two children** | Replace value with the **in-order successor** (smallest value in right subtree), then delete that successor |

### Step 5.1 — Add the `delete` method

Add this to `BST.java` **before** `main`:

```java
// ── DELETE ────────────────────────────────────────────────────────────────
public Node delete(Node root, int data) {
    if (root == null) return null;

    if (data < root.data) {
        root.left = delete(root.left, data);       // target is in left subtree
    } else if (data > root.data) {
        root.right = delete(root.right, data);     // target is in right subtree
    } else {
        // ── Node found ──────────────────────────────────────────────────
        // Case 1 & 2: zero or one child
        if (root.left == null)  return root.right;
        if (root.right == null) return root.left;

        // Case 3: two children
        // Find in-order successor (smallest node in right subtree)
        Node minNode = findMin(root.right);
        root.data = minNode.data;                  // copy successor's value here
        root.right = delete(root.right, minNode.data); // remove the successor
    }
    return root;
}
```

### Step 5.2 — Update `main` to test deletion

Add at the end of `main`:

```java
// Delete
System.out.println("\n--- Delete node 30 (two children) ---");
tree.root = tree.delete(tree.root, 30);
System.out.print("In-Order after delete: ");
tree.inOrder(tree.root);
System.out.println();
```

### Step 5.3 — Run and verify

```bash
docker run --rm -v "$(pwd)":/lab -w /lab \
  eclipse-temurin:21-jdk-alpine \
  sh -c "javac Node.java BST.java && java BST"
```

**Expected complete output:**
```
=== Binary Search Tree Lab ===

Inserting: 50, 30, 70, 20, 40, 60, 80
Root node: 50

In-Order   (sorted): 20 30 40 50 60 70 80 
Pre-Order  (root first): 50 30 20 40 70 60 80 
Post-Order (root last):  20 40 30 60 80 70 50 

--- Search ---
Search 40: true
Search 99: false

--- Min / Max ---
Minimum: 20

--- Delete node 30 (two children) ---
In-Order after delete: 20 40 50 60 70 80 
```

!!! question "What happened to node 30?"
    Node 30 had two children (20 and 40). Its in-order successor is **40** (the smallest value in its right subtree). Java replaced 30's value with 40, then deleted the original 40 node. The tree remains valid — notice 20 is still to the left of 40.

📸 **Screenshot checkpoint D** — complete output including delete result

---

## Part 6 — Challenge Exercises

Create a new file **`BSTChallenge.java`**:

```java
public class BSTChallenge {

    // Challenge 1: Count total nodes
    public static int countNodes(Node root) {
        if (root == null) return 0;
        return 1 + countNodes(root.left) + countNodes(root.right);
    }

    // Challenge 2: Height of the BST (longest path from root to leaf)
    public static int height(Node root) {
        if (root == null) return 0;
        return 1 + Math.max(height(root.left), height(root.right));
    }

    // Challenge 3: Validate whether a tree satisfies the BST property
    public static boolean isValidBST(Node root, Integer min, Integer max) {
        if (root == null) return true;
        if (min != null && root.data <= min) return false;
        if (max != null && root.data >= max) return false;
        return isValidBST(root.left, min, root.data)
            && isValidBST(root.right, root.data, max);
    }

    public static void main(String[] args) {
        BST tree = new BST();
        for (int v : new int[]{50, 30, 70, 20, 40, 60, 80}) {
            tree.root = tree.insert(tree.root, v);
        }

        System.out.println("=== BST Challenge Exercises ===\n");
        System.out.println("Total nodes : " + countNodes(tree.root));
        System.out.println("Tree height : " + height(tree.root));
        System.out.println("Valid BST?  : " + isValidBST(tree.root, null, null));
    }
}
```

**Compile and run:**

```bash
docker run --rm -v "$(pwd)":/lab -w /lab \
  eclipse-temurin:21-jdk-alpine \
  sh -c "javac Node.java BST.java BSTChallenge.java && java BSTChallenge"
```

**Expected output:**
```
=== BST Challenge Exercises ===

Total nodes : 7
Tree height : 3
Valid BST?  : true
```

📸 **Screenshot checkpoint E** — challenge output

---

## Cleanup

Stop and remove any running containers:

```bash
docker ps -a
docker rm $(docker ps -aq) 2>/dev/null || true
```

Remove the Docker image (optional — saves ~200 MB):

```bash
docker rmi eclipse-temurin:21-jdk-alpine
```

---

## BST Complexity Reference

| Operation | Average Case | Worst Case (degenerate/stick tree) |
|-----------|-------------|-------------------------------------|
| Insert | O(log n) | O(n) |
| Search | O(log n) | O(n) |
| Delete | O(log n) | O(n) |
| Traversal | O(n) | O(n) |
| Space | O(n) | O(n) |

!!! tip "Why worst case is O(n)"
    If you insert values in sorted order (1, 2, 3, 4 …), the BST degenerates into a linked list — every node only has a right child. Self-balancing trees (AVL, Red-Black) fix this by automatically rebalancing after inserts and deletes.

---

## Lab Assessment

### Screenshot Submission Checklist

Submit **five screenshots** to Canvas:

- [ ] **Screenshot A** — `docker pull` + `java --version` output
- [ ] **Screenshot B** — All three traversal outputs (In-Order, Pre-Order, Post-Order)
- [ ] **Screenshot C** — Search and minimum output
- [ ] **Screenshot D** — Complete output including delete result
- [ ] **Screenshot E** — Challenge exercises output

### Reflection Questions

Answer each question in **3–5 sentences** (40 points total):

1. **BST Property:** Explain in your own words why in-order traversal of a BST always produces a sorted sequence. Use the tree from this lab to illustrate your explanation.

2. **Search Efficiency:** A BST with 1,000,000 nodes can find any value in at most ~20 comparisons (log₂ 1,000,000 ≈ 20). Why is this so much faster than scanning an unsorted array? What property of the BST makes this possible?

3. **Delete Complexity:** When deleting a node with two children, why must we replace it with the in-order successor (smallest value in right subtree) instead of just removing it? What would happen to the BST property if we removed it directly?

4. **Real-World Application:** Identify one real-world software system (e.g., a database, file system, programming language runtime, or security tool) that uses a BST or a BST-variant internally. Describe what data it stores and why a BST is an appropriate choice for that use case.

!!! tip "Grading Rubric"
    Screenshots 40 pts (8 pts each × 5) + Challenge Output 20 pts + Reflection Questions 40 pts (10 pts each) = **100 pts**
