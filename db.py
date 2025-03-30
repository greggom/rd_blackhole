import os.path

def create_rd_db():
    if os.path.exists('InRD.json'):
        pass
    else:
        print('Database not created. Creating now.')
        with open('InRD.json', 'w') as file:
            file.write('{}')
        print('Database has been created')