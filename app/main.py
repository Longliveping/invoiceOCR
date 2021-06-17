from flask import Flask
from flask_restful import Api as FlaskRestfulAPI, Resource, reqparse, abort
from werkzeug.datastructures import FileStorage
from invoice_ocr import invoice_data

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
        return 'Hello fp'

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
        with open('image.png', 'wb') as f:
            image.save(f)

        passed, fp = invoice_data('image.png')
        if passed[0]:
            keys = ['发票类型','发票代码','发票号码','开票日期','校验码','金额','价税合计']
            dic = dict(zip(keys, fp))
            print(dic)
            return (dic)
        else:
            return 'NOT OK'


api.add_resource(UploadImage, '/upload_image')

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=8080)