from flask import Flask
from flask_restful import Api as FlaskRestfulAPI, Resource, reqparse, abort
from werkzeug.datastructures import FileStorage
from invoice_ocr import invoice_data
import pandas as pd

## config
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']
FILE_CONTENT_TYPES = { # these will be used to set the content type of S3 object. It is binary by default.
    'jpg': 'image/jpg',
    'jpeg': 'image/jpeg',
    'png': 'image/png'
}

## app initilization
app = Flask(__name__)
app.config.from_object(__name__)
# app.config['JSON_AS_ASCII'] = False

## extensions
api = FlaskRestfulAPI(app)


class FileStorageArgument(reqparse.Argument):
    """This argument class for flask-restful will be used in
    all cases where file uploads need to be handled."""

    def convert(self, value, op):
        if self.type is FileStorage:  # only in the case of files
            # this is done as self.type(value) makes the name attribute of the
            # FileStorage object same as argument name and value is a FileStorage
            # object itself anyways
            return value

        # called so that this argument class will also be useful in
        # cases when argument type is not a file.
        super(FileStorageArgument, self).convert(*args, **kwargs)


# API Endpoints

class UploadImage(Resource):

    put_parser = reqparse.RequestParser(argument_class=FileStorageArgument)
    put_parser.add_argument('image', required=True, type=FileStorage, location='files')

    def get(self):
        return 'Hello'

    def post(self):
        #TODO: a check on file size needs to be there.
        args = self.put_parser.parse_args()
        image = args['image']

        # check logo extension
        extension = image.filename.rsplit('.', 1)[1].lower()
        print('file ',image)
        if '.' in image.filename and not extension in app.config['ALLOWED_EXTENSIONS']:
            abort(400, message="File extension is not one of our supported types.")

        # create a file object of the image
        with open('../image.png', 'wb') as f:
            image.save(f)

        if invoice_data('../image.png'):
            df = pd.read_csv('../invoice.csv', index_col=0, dtype=str)
            df.index = ['发票代码','发票号码','开票日期','校验码','金额']
            dic = {
                df.index[0]: df['0'][0],
                df.index[1]: df['0'][1],
                df.index[2]: df['0'][2],
                df.index[3]: df['0'][3],
                df.index[4]: f"{float(df['0'][4]):.2f}"
            }

            print(dic)

            return (dic)
        else:
            return 'Not OK'


class Main(Resource):
    def get(self):
        return "Hello World"

api.add_resource(UploadImage, '/upload_image')
api.add_resource(Main, '/')

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)