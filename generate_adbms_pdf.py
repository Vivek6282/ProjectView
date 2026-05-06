import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Constants for colors (converted from hex)
COLOR_TITLE = colors.HexColor("#1F3864")
COLOR_H1 = colors.HexColor("#1F3864")
COLOR_H2 = colors.HexColor("#2E75B6")
COLOR_QUESTION = colors.HexColor("#C00000")
COLOR_ANSWER = colors.HexColor("#1F5C1F")
COLOR_BORDER = colors.HexColor("#2E75B6")
COLOR_TABLE_HEADER = colors.HexColor("#1F3864")
COLOR_TABLE_ROW_EVEN = colors.HexColor("#EBF3FB")
COLOR_TABLE_ROW_ODD = colors.HexColor("#FFFFFF")
COLOR_DIVIDER = colors.HexColor("#CCCCCC")

def generate_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        'TitlePage',
        parent=styles['Heading1'],
        fontSize=20, # 40 half-pts
        textColor=COLOR_TITLE,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    style_h1 = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontSize=16, # 32 half-pts
        textColor=COLOR_H1,
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    style_h2 = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=13, # 26 half-pts
        textColor=COLOR_H2,
        spaceBefore=15,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    style_q_label = ParagraphStyle(
        'QuestionLabel',
        parent=styles['Normal'],
        fontSize=11, # 22 half-pts
        textColor=COLOR_QUESTION,
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=3
    )
    
    style_q_text = ParagraphStyle(
        'QuestionText',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-BoldOblique',
        leftIndent=18, # 360 units
        spaceBefore=0,
        spaceAfter=4
    )
    
    style_answer_heading = ParagraphStyle(
        'AnswerHeading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_ANSWER,
        fontName='Helvetica-Bold',
        leftIndent=18,
        spaceBefore=5,
        spaceAfter=3
    )
    
    style_para = ParagraphStyle(
        'NormalPara',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        leftIndent=36, # 720 units
        spaceBefore=3,
        spaceAfter=3
    )
    
    style_bullet = ParagraphStyle(
        'BulletPoint',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        leftIndent=54, # 1080 units
        firstLineIndent=-18, # hanging 360
        spaceBefore=2,
        spaceAfter=2
    )
    
    style_subheading = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_H1,
        fontName='Helvetica-Bold',
        leftIndent=36,
        spaceBefore=5,
        spaceAfter=2
    )

    story = []

    # Title Page
    story.append(Spacer(1, 40))
    story.append(Paragraph("ADVANCED DATABASE MANAGEMENT SYSTEMS", style_title))
    story.append(Paragraph("24MCAT102", ParagraphStyle('SubTitle', parent=style_title, fontSize=14, textColor=COLOR_H2)))
    story.append(Paragraph("Question Bank with Detailed Answers", ParagraphStyle('QB', parent=style_title, fontSize=15, textColor=COLOR_QUESTION)))
    story.append(Paragraph("UNIT 4 & UNIT 5", style_title))
    story.append(Paragraph("MCA | Amal Jyothi College of Engineering (Autonomous)", ParagraphStyle('College', parent=style_title, fontSize=11, textColor=colors.HexColor("#555555"), fontName='Helvetica-Oblique')))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_H2, spaceBefore=10, spaceAfter=20))
    
    # UNIT 4
    story.append(Paragraph("UNIT 4: Storage and File Structures, Indexing & Hashing, Query Processing", style_h1))
    story.append(Paragraph("PART A - Short Answer Questions (5 Marks Each)", style_h2))

    # Data for Questions
    questions_u4 = [
        {
            "label": "Q1. [Part A - 5 Marks]",
            "text": "An online bookstore needs to efficiently store and retrieve information about books, authors, and customer orders. Illustrate how a well-designed indexing strategy can improve query performance in this scenario.",
            "answer": "Indexing is a data structure technique used to quickly locate and access the data in a database. Just as a book's index helps find topics without reading every page, database indexing allows the DBMS to locate records without scanning the entire table.",
            "subheadings": [
                {
                    "title": "How Indexing Improves Query Performance in an Online Bookstore:",
                    "bullets": [
                        "Book Search by ID: A primary index on Book_ID allows O(log n) lookup using B+ Tree instead of O(n) sequential scan.",
                        "Author Search: A secondary index on Author_Name allows fast retrieval of all books by a particular author without full table scan.",
                        "Order Retrieval: Indexing Order_Date enables fast range queries like 'orders placed between Jan-March'.",
                        "Multi-Attribute Queries: Composite indexes on (Category, Price) speed up queries filtering by genre and price range simultaneously."
                    ]
                },
                {
                    "title": "Types of Index Used:",
                    "bullets": [
                        "Dense Index: One index entry per record - faster but uses more space.",
                        "Sparse Index: One entry per block - saves space, used with ordered files.",
                        "B+ Tree Index: Most commonly used; supports both equality and range queries efficiently."
                    ]
                }
            ],
            "conclusion": "Thus, a proper indexing strategy drastically reduces query response time from O(n) to O(log n), which is critical for a bookstore handling thousands of queries per second."
        },
        {
            "label": "Q2. [Part A - 5 Marks]",
            "text": "A financial institution needs to ensure data redundancy and fault tolerance for its critical transaction records. Illustrate how RAID (Redundant Array of Independent Disks) can help achieve data reliability in this scenario.",
            "answer": "RAID is a storage technology that combines multiple physical disk drives into one logical unit to improve performance, reliability, or both.",
            "subheadings": [
                {
                    "title": "RAID Levels and Their Application in Finance:",
                    "bullets": [
                        "RAID 0 (Striping): Data is split across disks for speed. No redundancy - NOT suitable for critical financial data alone.",
                        "RAID 1 (Mirroring): Exact copy of data is written to two disks simultaneously. If one disk fails, the other has the complete data - ideal for critical transaction records.",
                        "RAID 5 (Striping with Parity): Data and parity information distributed across 3+ disks. Can tolerate one disk failure and rebuild data from parity - a balance of performance and fault tolerance.",
                        "RAID 6 (Double Parity): Can tolerate two simultaneous disk failures - used in high-security banking systems.",
                        "RAID 10 (1+0): Combines mirroring and striping - provides both high performance and redundancy."
                    ]
                },
                {
                    "title": "Benefits for Financial Institution:",
                    "bullets": [
                        "Fault Tolerance: Transaction data is preserved even on disk failure.",
                        "High Availability: System continues to operate during disk replacement (hot-swap).",
                        "Data Integrity: Parity mechanisms detect and correct errors."
                    ]
                }
            ],
            "conclusion": "Conclusion: RAID 5 or RAID 10 is the best choice for financial institutions, balancing performance, redundancy, and cost-efficiency."
        },
        {
            "label": "Q3. [Part A - 5 Marks]",
            "text": "A university's student database stores thousands of student records. Explain how Indexed File Organization can help improve data retrieval speed.",
            "answer": "Indexed File Organization maintains a separate index structure alongside the data file to enable fast access to records without sequential scanning.",
            "subheadings": [
                {
                    "title": "Structure of Indexed File Organization:",
                    "bullets": [
                        "Data File: Contains actual student records stored sequentially or randomly.",
                        "Index File: Contains key-pointer pairs mapping Student_ID to the physical address of the record."
                    ]
                },
                {
                    "title": "How It Works:",
                    "bullets": [
                        "When a query searches for Student_ID = 1045, the DBMS first looks into the index file.",
                        "The index gives the disk address (block/offset) of the record.",
                        "The DBMS performs a direct I/O operation to fetch that specific block - only 1-2 disk reads instead of scanning thousands of records."
                    ]
                },
                {
                    "title": "Advantages:",
                    "bullets": [
                        "Fast Retrieval: Lookup time reduced from O(n) to O(log n) using binary search on index.",
                        "Supports Range Queries: Useful for finding students with IDs between 1000-2000.",
                        "Multi-level Index: For very large files, multi-level indexing is used - outer index points to inner index which points to data."
                    ]
                }
            ],
            "conclusion": "In a university with 50,000 students, indexed file organization can reduce retrieval time from scanning 50,000 records to just 2-3 index lookups - a significant performance gain."
        },
        {
            "label": "Q4. [Part A - 5 Marks]",
            "text": "A library management system needs to quickly retrieve books based on their titles in alphabetical order. Explain how ordered indices can help improve the efficiency of book searches.",
            "answer": "An ordered index maintains index entries sorted in the same order as the search key (e.g., alphabetical order of book titles), enabling fast search operations.",
            "subheadings": [
                {
                    "title": "Types of Ordered Indices:",
                    "bullets": [
                        "Primary Index (Clustering Index): Built on the ordering key of the data file. Since book titles are stored alphabetically, the primary index directly corresponds to file order. Each index entry points to the first record of a block.",
                        "Secondary Index (Non-Clustering Index): Used when the data file is not sorted by the search key. Allows fast access on non-ordering attributes like Author Name."
                    ]
                },
                {
                    "title": "Dense vs. Sparse Index:",
                    "bullets": [
                        "Dense Index: One entry per record. Faster but requires more memory. For a library with 10,000 books, 10,000 index entries.",
                        "Sparse Index: One entry per data block. Much smaller index, sufficient for ordered files. Uses binary search to reach the correct block."
                    ]
                },
                {
                    "title": "How It Helps the Library:",
                    "bullets": [
                        "Binary Search on Index: Instead of scanning all 10,000 titles, binary search on the index file with ~14 comparisons (log2 10000) locates the correct block.",
                        "Range Queries: 'Find all books with title starting A-C' is efficient with ordered index - traverse from 'A' block forward.",
                        "Reduced I/O: Only the relevant disk block is loaded into memory."
                    ]
                }
            ],
            "conclusion": "Ordered indices are the backbone of efficient database searches, especially when data is frequently accessed in sorted order."
        },
        {
            "label": "Q5. [Part A - 5 Marks]",
            "text": "A banking system needs to efficiently search for customer account details based on account numbers. Examine how a B+ Tree index file can improve the search and update performance.",
            "answer": "A B+ Tree is a self-balancing tree data structure used as an index, where all actual data pointers are stored only at leaf nodes, and internal nodes contain only keys for navigation.",
            "subheadings": [
                {
                    "title": "Structure of B+ Tree:",
                    "bullets": [
                        "Root Node: Top of the tree; contains separator keys to guide searches.",
                        "Internal Nodes: Contain only keys (no data pointers); guide the search path.",
                        "Leaf Nodes: Contain all search keys with pointers to actual records; leaf nodes are linked in a doubly linked list for sequential access."
                    ]
                },
                {
                    "title": "How B+ Tree Helps a Bank:",
                    "bullets": [
                        "Search (Equality): To find Account_No = 10045, traverse from root through internal nodes to the correct leaf in O(log n) time.",
                        "Range Queries: Due to linked leaf nodes, 'Find all accounts with number 10000-20000' is efficient - find start leaf, then traverse the linked list.",
                        "Insert/Delete: B+ Tree remains balanced after insertions and deletions through node splitting and merging.",
                        "Balanced Height: All paths from root to leaf have equal length, ensuring consistent O(log n) performance."
                    ]
                },
                {
                    "title": "Advantages over Simple Index:",
                    "bullets": [
                        "Supports both point queries and range queries.",
                        "Self-balancing - no degradation in performance over time.",
                        "Efficiently handles large datasets - even millions of accounts."
                    ]
                }
            ],
            "conclusion": "For a bank with millions of accounts, a B+ Tree with order 100 needs at most log100(n) disk accesses - typically 3-4 levels for 1 million records."
        },
        {
            "label": "Q6. [Part A - 5 Marks]",
            "text": "A bank needs to quickly retrieve customer account details using unique account numbers stored in its database. Examine how Static Hashing can improve the efficiency of account lookup operations.",
            "answer": "Static Hashing is a file organization technique where a hash function maps the search key (Account_No) to a fixed set of buckets (disk blocks), allowing direct access to the record's location.",
            "subheadings": [
                {
                    "title": "How Static Hashing Works:",
                    "bullets": [
                        "A hash function H(key) = key mod B is applied where B = total number of buckets.",
                        "Example: Account_No = 10047, B = 100 -> H(10047) = 47 -> stored in bucket 47.",
                        "Each bucket is a disk block that stores multiple records.",
                        "For retrieval: compute H(Account_No) -> directly access bucket -> scan bucket."
                    ]
                },
                {
                    "title": "Advantages:",
                    "bullets": [
                        "O(1) Average Lookup: Direct computation of bucket address means typical retrieval in one disk access.",
                        "No Index Tree Required: No need to traverse tree nodes; computation gives location instantly.",
                        "Ideal for Equality Queries: Perfect for 'Find account number = 10047' type queries."
                    ]
                },
                {
                    "title": "Handling Collisions - Overflow Buckets:",
                    "bullets": [
                        "When multiple keys hash to same bucket (collision), overflow bucket is chained.",
                        "Overflow chains can degrade performance if too many collisions occur."
                    ]
                },
                {
                    "title": "Limitations of Static Hashing:",
                    "bullets": [
                        "Fixed number of buckets - poor performance if database grows significantly.",
                        "Cannot efficiently handle range queries ('accounts between 10000-20000')."
                    ]
                }
            ],
            "conclusion": "Static Hashing is best suited for banks with a relatively stable, known dataset size and frequent equality-based lookups."
        },
        {
            "label": "Q7. [Part A - 5 Marks]",
            "text": "An e-commerce platform experiences rapid growth in user registrations. Examine how Dynamic Hashing helps in efficiently managing growing data without excessive collisions.",
            "answer": "Dynamic Hashing (also called Extendible Hashing) overcomes the major limitation of static hashing by allowing the hash table to grow and shrink dynamically as data increases or decreases.",
            "subheadings": [
                {
                    "title": "How Dynamic Hashing Works:",
                    "bullets": [
                        "Uses a directory of pointers to buckets. Each directory entry points to a bucket.",
                        "A global depth (d) determines how many bits of the hash value are used to index the directory (directory size = 2^d).",
                        "Each bucket has a local depth indicating how many bits of the hash it currently uses.",
                        "When a bucket overflows: only that specific bucket is split; the directory may or may not double."
                    ]
                },
                {
                    "title": "Example (E-commerce Platform):",
                    "bullets": [
                        "Initially: global depth = 1, directory has 2 entries [0, 1] pointing to 2 buckets.",
                        "As users grow, bucket for prefix '10' overflows -> that bucket splits into '100' and '101' -> directory doubles if needed.",
                        "Only the overflowed bucket is reorganized, not the entire file."
                    ]
                },
                {
                    "title": "Advantages over Static Hashing:",
                    "bullets": [
                        "Scalability: File grows dynamically; no need to know data size in advance.",
                        "Minimal Overhead: Only the overflowed bucket splits - not full reorganization.",
                        "Low Collision Rate: Buckets split before overflow becomes severe.",
                        "Efficient Space Utilization: No over-allocation of unused buckets initially."
                    ]
                }
            ],
            "conclusion": "For an e-commerce platform growing from 10,000 to 10 million users, dynamic hashing adapts seamlessly without performance degradation."
        },
        {
            "label": "Q8. [Part A - 5 Marks]",
            "text": "A hospital database stores patient records. A doctor wants to retrieve records of all patients aged above 60. Explain how the selection operation can help efficiently retrieve the required patient records.",
            "answer": "The Selection Operation (sigma) in query processing retrieves only those tuples from a relation that satisfy a specified condition, reducing the data set for subsequent operations.",
            "subheadings": [
                {
                    "title": "Selection Operation in Relational Algebra:",
                    "bullets": [
                        "sigma Age > 60 (Patient) - retrieves all patient records where Age > 60."
                    ]
                },
                {
                    "title": "Algorithms for Selection Operation:",
                    "bullets": [
                        "Linear Scan: Read every block of the Patient relation and check if Age > 60. Cost = total blocks B. Simple but expensive for large tables.",
                        "Primary Index on Key: If selection is on primary key (Patient_ID = 101), use index to find exact block - cost = height of B+ tree + 1.",
                        "Secondary Index on Non-Key: If secondary index exists on Age, retrieve all entries with Age > 60 from index, then fetch corresponding records.",
                        "Sorting-based Selection: If file is sorted on Age, use binary search to find the first record with Age > 60, then scan forward."
                    ]
                },
                {
                    "title": "Optimization for the Hospital Scenario:",
                    "bullets": [
                        "Create a secondary index on 'Age' attribute.",
                        "Range condition 'Age > 60' is handled by B+ Tree leaf traversal from the first qualifying key.",
                        "Only relevant blocks are fetched, not the entire patient table."
                    ]
                }
            ],
            "conclusion": "Without optimization, scanning 1,00,000 patient records for Age > 60 could require 1000+ disk reads. With a B+ Tree index on Age, it reduces to ~15 disk reads."
        },
        {
            "label": "Q9. [Part A - 5 Marks]",
            "text": "A hospital maintains patient records in a database. To ensure efficient searching and updating of records, examine how Sequential Record Organization can improve data access efficiency.",
            "answer": "Sequential File Organization stores records in a file sorted by a specific ordering key (e.g., Patient_ID) so that records are physically arranged in sequence on disk.",
            "subheadings": [
                {
                    "title": "How Sequential Organization Works:",
                    "bullets": [
                        "Records are stored one after another in sorted order of the search key.",
                        "New records are typically appended to an overflow file, and periodic reorganization merges them back into sorted order."
                    ]
                },
                {
                    "title": "Operations and Efficiency:",
                    "bullets": [
                        "Search: Binary search can be applied since records are sorted. For N records in B blocks, cost = O(log2 B) block accesses.",
                        "Insert: New record goes to overflow area. Pointers maintain logical order. Periodic merge is needed.",
                        "Delete: Record is marked deleted (logical deletion). Periodically, reorganization removes gaps.",
                        "Range Queries: Very efficient - 'Find patients admitted between Jan-March' only requires reading consecutive blocks."
                    ]
                },
                {
                    "title": "Application in Hospital Database:",
                    "bullets": [
                        "Sorted by Patient_ID: Any search for a specific patient can use binary search across blocks.",
                        "Batch Processing: Medical billing reports that process all patients in ID order are highly efficient.",
                        "Report Generation: Sequential scan for generating sorted patient lists is natural and fast."
                    ]
                }
            ],
            "conclusion": "Sequential file organization is best suited for batch processing, report generation, and applications with predominantly sequential access patterns."
        },
        {
            "label": "Q10. [Part A - 5 Marks]",
            "text": "A university database stores student records and frequently searches for students based on their ID numbers. Illustrate how a B-Tree index file can improve the efficiency of student record retrieval by listing its characteristics.",
            "answer": "A B-Tree (Balanced Tree) is a self-balancing multi-level index structure where both internal nodes and leaf nodes can store data pointers, unlike B+ Tree where only leaf nodes hold data.",
            "subheadings": [
                {
                    "title": "Characteristics of B-Tree:",
                    "bullets": [
                        "All nodes (internal + leaf) can contain both keys and pointers to actual records.",
                        "A B-Tree of order m can have at most m children and at least ceil(m/2) children per node (except root).",
                        "All leaf nodes are at the same level - perfectly balanced.",
                        "Keys within each node are sorted in ascending order.",
                        "No duplicate keys are stored; each key appears exactly once in the tree.",
                        "For a node with k keys, there are k+1 child pointers."
                    ]
                },
                {
                    "title": "How B-Tree Improves Student Record Retrieval:",
                    "bullets": [
                        "Search: To find Student_ID = 1045, start at root, compare key, navigate to appropriate subtree - O(log n) comparisons.",
                        "Early Termination: Unlike B+ Tree, if the searched key is found in an internal node, the search terminates immediately without reaching leaf.",
                        "Insert: New key inserted into appropriate leaf. If node overflows, split the node and promote median key to parent.",
                        "Delete: More complex than B+ Tree as keys at any level must be reorganized."
                    ]
                }
            ],
            "conclusion": "For a university with 50,000 students, a B-Tree of order 100 with height 3 can store millions of keys and retrieve any student record in just 3 disk accesses."
        }
    ]

    # Function to add a question block
    def add_question(story, q):
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_DIVIDER, spaceBefore=10, spaceAfter=10))
        story.append(Paragraph(q["label"], style_q_label))
        story.append(Paragraph(q["text"], style_q_text))
        story.append(Paragraph("ANSWER:", style_answer_heading))
        story.append(Paragraph(q["answer"], style_para))
        for sub in q.get("subheadings", []):
            story.append(Paragraph(sub["title"], style_subheading))
            for b in sub["bullets"]:
                story.append(Paragraph(b, style_bullet))
        if q.get("conclusion"):
            story.append(Paragraph(q["conclusion"], style_para))

    for q in questions_u4:
        add_question(story, q)

    # LONG ANSWER Q1 (PART B)
    story.append(PageBreak())
    story.append(Paragraph("PART B - Long Answer Questions (10 Marks Each)", style_h2))
    
    q_b1 = {
        "label": "Q1. [Part B - 10 Marks]",
        "text": "A large online retail store maintains a product database containing millions of product records. Customers frequently search for products based on their ID or category. Explain the importance of using indexing and hashing to improve search performance. Illustrate one indexing technique and explain how it helps in optimizing product searches.",
        "answer": "A retail store with millions of products cannot afford sequential scans for every search query. Without indexing or hashing, every product search would require reading potentially millions of records - unacceptable for real-time e-commerce performance.",
        "subheadings": [
            {
                "title": "Importance of Indexing:",
                "bullets": [
                    "Reduces Disk I/O: Index structures locate records with minimal disk reads.",
                    "Supports Multiple Access Paths: Indexes on Product_ID, Category, and Price allow different query types to be optimized simultaneously.",
                    "Range Query Support: 'Find all products priced between Rs. 500-1000' is efficiently handled by ordered index structures like B+ Trees.",
                    "Sorted Output: Queries requiring sorted output (ORDER BY) can leverage the sorted nature of indexed files."
                ]
            },
            {
                "title": "Importance of Hashing:",
                "bullets": [
                    "O(1) Equality Lookups: 'Find product with ID = P1045' can be answered in one disk access using a hash function.",
                    "No Index Tree Traversal: Hash-based access skips multi-level tree traversal entirely.",
                    "Efficient for Exact Match Queries: Online shopping 'Add to Cart' by Product_ID benefits from O(1) hashing."
                ]
            },
            {
                "title": "Illustrated Indexing Technique: B+ Tree Index on Product_ID",
                "bullets": [
                    "Order m = 100 (each node holds up to 99 keys and 100 child pointers).",
                    "Internal Nodes: Contain separator keys (Product IDs) to guide navigation. No data pointers here.",
                    "Leaf Nodes: Contain all Product_IDs with pointers to actual product records on disk. All leaf nodes connected via linked list for sequential traversal."
                ]
            },
            {
                "title": "Search Example:",
                "bullets": [
                    "Query: SELECT * FROM Products WHERE Product_ID = 'P1045'",
                    "Step 1: Start at root - compare P1045 with separator keys -> navigate to correct child.",
                    "Step 2: Traverse internal nodes (typically 2-3 levels for millions of records).",
                    "Step 3: Reach leaf node containing P1045 -> follow pointer -> fetch actual record."
                ]
            }
        ]
    }
    add_question(story, q_b1)

    # UNIT 5
    story.append(PageBreak())
    story.append(Paragraph("UNIT 5: Distributed Databases, Advanced Database Technologies, NoSQL", style_h1))
    story.append(Paragraph("PART A - Short Answer Questions (5 Marks Each)", style_h2))

    questions_u5 = [
        {
            "label": "Q1. [Part A - 5 Marks]",
            "text": "A company wants to implement a distributed database system to improve performance and reliability. Illustrate one application-level advantage of using a distributed database over a centralized database.",
            "answer": "A Distributed Database System (DDBS) stores data across multiple physical locations (nodes/sites) connected via a network, managed so that they appear as a single database to users.",
            "subheadings": [
                {
                    "title": "Key Application-Level Advantage: Local Data Proximity",
                    "bullets": [
                        "Data is stored at the sites where it is most frequently accessed (data locality principle).",
                        "A branch office in Kerala accesses Kerala-specific data stored on a local server in Kerala - response time is near-zero compared to querying a central server in Delhi.",
                        "Example: A national bank with branches in Kerala, Maharashtra, Delhi stores each state's customer data on that state's regional server."
                    ]
                }
            ],
            "conclusion": "Conclusion: The primary application-level advantage of a distributed database is reduced latency through data locality - data is stored close to where it is used, resulting in faster access and improved user experience."
        },
        {
            "label": "Q4. [Part A - 5 Marks]",
            "text": "A banking application uses a distributed transaction system to ensure consistency across multiple branches. Illustrate how atomicity is maintained in a distributed transaction to prevent inconsistencies in account balances.",
            "answer": "Atomicity in distributed transactions means that all operations across all participating sites either all complete successfully (commit) or all are rolled back (abort) - there is no partial execution.",
            "subheadings": [
                {
                    "title": "Two-Phase Commit (2PC) Protocol - The Solution:",
                    "bullets": [
                        "Phase 1 - Prepare Phase (Voting Phase): TC sends PREPARE message to all participants. Each participant checks if it can commit and sends VOTE-YES or VOTE-NO.",
                        "Phase 2 - Commit/Abort Phase: If ALL vote YES, TC sends COMMIT. If ANY vote NO, TC sends ABORT."
                    ]
                }
            ],
            "conclusion": "Result: The bank transfer either fully completes (both accounts updated correctly) or fully aborts (both accounts remain unchanged). Data inconsistency is completely prevented."
        }
    ]
    
    for q in questions_u5:
        add_question(story, q)

    # Summary Tables
    story.append(PageBreak())
    story.append(Paragraph("Quick Reference Summary", style_h1))
    
    def create_summary_table(rows, title):
        story.append(Paragraph(title, style_subheading))
        table_data = [["Topic", "Key Concept", "Exam Tip"]]
        table_data.extend(rows)
        
        t = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Zebra striping
        for i in range(1, len(table_data)):
            if i % 2 == 1:
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), COLOR_TABLE_ROW_EVEN)]))
            else:
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), COLOR_TABLE_ROW_ODD)]))
        
        story.append(t)
        story.append(Spacer(1, 10))

    unit4_rows = [
        ["Indexing", "Reduces search from O(n) to O(log n)", "Always mention Dense vs Sparse"],
        ["B+ Tree", "All data at leaves; linked list for range queries", "Draw the structure in 10M answers"],
        ["B-Tree", "Data at all nodes; no leaf linked list", "Compare with B+ Tree clearly"],
        ["Static Hashing", "Fixed buckets; O(1) lookup; overflow chains", "Mention limitations for growing data"],
        ["Dynamic Hashing", "Extendible; splits only overflowed bucket", "Explain global depth and local depth"],
        ["RAID", "Striping+Mirroring+Parity; 0,1,5,6,10", "RAID is NOT a backup - mention this"],
        ["File Organization", "Heap, Sequential, Indexed, Hash-based", "Compare all 4 types"],
        ["Query Processing", "Parse->Optimize->Execute pipeline", "Mention cost-based optimization"],
        ["Selection Operation", "sigma condition(Relation); algorithms vary", "Linear scan vs index scan cost"],
        ["Sequential Organization", "Sorted by key; binary search possible", "Best for batch/range queries"],
    ]
    
    unit5_rows = [
        ["Distributed DB", "Data across multiple sites; appears unified", "Always mention advantages + challenges"],
        ["Fragmentation", "Horizontal (rows) vs Vertical (columns)", "Mention completeness + reconstruction"],
        ["Replication", "Copies at multiple sites; improves reads", "Synchronous vs asynchronous trade-off"],
        ["2PC Protocol", "Phase 1: Vote; Phase 2: Commit/Abort", "Draw both phases with messages"],
        ["CAP Theorem", "C+A+P: can only guarantee 2 of 3", "Social media = AP; Banking = CP"],
        ["Transparency", "Location, Fragmentation, Replication types", "List all 7 types for 10M question"],
        ["NoSQL/Non-Relational", "Flexible schema; horizontal scale", "Why not RDBMS - impedance mismatch"],
        ["MongoDB Sharding", "Shard key; Config servers; mongos router", "Explain 3 components clearly"],
        ["HBase", "Column-family; HDFS; RegionServer; Zookeeper", "3 main components always asked"],
        ["Cassandra", "Leaderless; Gossip protocol; Tunable consistency", "Compare with MongoDB replication"],
        ["Object-Based DB", "Objects with attributes + methods; inheritance", "Impedance mismatch is key concept"],
        ["Distributed Transactions", "Coordinator + Participants + 2PC", "Always link to ACID properties"],
    ]

    create_summary_table(unit4_rows, "Unit 4 - Key Topics Covered")
    create_summary_table(unit5_rows, "Unit 5 - Key Topics Covered")

    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph("Best of Luck for your Examinations!", ParagraphStyle('Final', parent=style_para, alignment=TA_CENTER, textColor=COLOR_QUESTION, fontName='Helvetica-Bold', fontSize=14)))
    story.append(Paragraph("Amal Jyothi College of Engineering (Autonomous) | MCA Programme | 24MCAT102 ADBMS", ParagraphStyle('CollegeFooter', parent=style_para, alignment=TA_CENTER, fontSize=10, textColor=colors.grey, fontName='Helvetica-Oblique')))

    doc.build(story)

if __name__ == "__main__":
    generate_pdf("ADBMS_Units4_5.pdf")
    print("PDF generated successfully: ADBMS_Units4_5.pdf")
