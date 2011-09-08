# -*- mode: Python; coding: utf-8 -*-

# Copyright (c) 2002-2011 "Neo Technology,"
# Network Engine for Objects in Lund AB [http://neotechnology.com]
#
# This file is part of Neo4j.
#
# Neo4j is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import unit_tests
import tempfile, os

class ExamplesTest(unit_tests.GraphDatabaseTest):
    
    def test_hello_world(self):
        folder_to_put_db_in = tempfile.mkdtemp()
        try:
            # START SNIPPET: helloworld
            from neo4j import GraphDatabase
            
            # Create a database
            db = GraphDatabase(folder_to_put_db_in)
            
            # All write operations happen in a transaction
            with db.transaction:
                firstNode = db.node(name='Hello')
                secondNode = db.node(name='world!')
                
                # Create a relationship with type 'knows'
                relationship = firstNode.knows(secondNode, name='graphy')
                
            # Read operations can happen anywhere
            message = ' '.join([firstNode['name'], relationship['name'], secondNode['name']])
            
            print message
            
            # Delete the data
            with db.transaction:
                firstNode.knows.single.delete()
                firstNode.delete()
                secondNode.delete()
            
            # Always shut down your database when your application exits
            db.shutdown()
            # END SNIPPET: helloworld
        finally:
           if os.path.exists(folder_to_put_db_in):
              import shutil
              shutil.rmtree(folder_to_put_db_in)
              
        self.assertEqual(message, 'Hello graphy world!')
    
    def test_invoice_app(self):
        folder_to_put_db_in = tempfile.mkdtemp()
        try:
            # START SNIPPET: invoiceapp
            from neo4j import GraphDatabase, INCOMING, Evaluation
            from datetime import date
            import time
            
            # Create a database
            db = GraphDatabase(folder_to_put_db_in)
            
            # Create some base data
            with db.transaction:
                
                # A node to connect customers to
                customers = db.node()
                
                # A node to connect invoices to
                invoices = db.node()
                
                # Connected to the reference node, so
                # that we can always find it.
                db.reference_node.CUSTOMERS(customers)
                db.reference_node.INVOICES(invoices)
                
                # An index, helps us rapidly look up customers
                customer_idx = db.node.indexes.create('customers')
            
            
            # Some domain logic
            
            def create_customer(name):
                with db.transaction:                    
                    customer = db.node(name=name)
                    customers.CUSTOMER(customer)
                    
                    # Index the customer by name
                    customer_idx['name'][name] = customer
                return customer
                
            def create_invoice(customer, amount):
                with db.transaction:
                    invoice = db.node(amount=amount)
                    invoices.INVOICE(invoice)
                    
                    invoice.RECIPIENT(customer)
                return customer
                
            def get_customer(name):
                return customer_idx['name'][name].single
                
            def get_invoices_with_amount_over(customer, min_sum):
                def evaluator(path):
                    node = path.end
                    if node.has_key('amount') and node['amount'] > min_sum:
                        return Evaluation.INCLUDE_AND_CONTINUE
                    return Evaluation.EXCLUDE_AND_CONTINUE
                
                return db.traversal()\
                         .relationships('RECIPIENT', INCOMING)\
                         .evaluator(evaluator)\
                         .traverse(customer)\
                         .nodes()
            
            
            # Create some domain data
            
            for name in ['Acme Inc.', 'Example Ltd.']:
               create_customer(name)
            
            for relationship in customers.CUSTOMER:
               for i in range(1,12):
                   create_invoice(relationship.end, 100 * i)
                   
                   
            # Find invoices over a given sum for a given customer
            
            large_invoices = get_invoices_with_amount_over(get_customer('Acme Inc.'), 500)
            # END SNIPPET: invoiceapp
            
            self.assertEqual(len(large_invoices), 6)
            # Always shut down your database when your application exits
            db.shutdown()
        finally:
           if os.path.exists(folder_to_put_db_in):
              import shutil
              shutil.rmtree(folder_to_put_db_in)

if __name__ == '__main__':
    unit_tests.unittest.main()