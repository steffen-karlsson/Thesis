package dk.steffenkarlsson.sofa.bdae.request;

import com.squareup.okhttp.RequestBody;

import dk.steffenkarlsson.sofa.networking.ParserException;
import dk.steffenkarlsson.sofa.networking.PutRequest;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class InitializeRequest extends PutRequest<Boolean> {

    public InitializeRequest() {
        super(URLUtils.initializeWithInstanceUrl());
    }

    @Override
    protected Boolean parseHttpResponseBody(String body) throws ParserException {
        return Boolean.valueOf(body);
    }

    @Override
    protected RequestBody getData() {
        return RequestBody.create(text, "");
    }
}
