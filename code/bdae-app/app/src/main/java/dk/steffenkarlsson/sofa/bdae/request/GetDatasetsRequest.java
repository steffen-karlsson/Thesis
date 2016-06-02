package dk.steffenkarlsson.sofa.bdae.request;

import com.google.gson.reflect.TypeToken;

import java.util.List;

import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.networking.GetRequest;
import dk.steffenkarlsson.sofa.networking.ParserException;
import dk.steffenkarlsson.sofa.networking.RequestUtils;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class GetDatasetsRequest extends GetRequest<List<Dataset>> {

    public GetDatasetsRequest() {
        super(URLUtils.getDatasetsUrl());
    }

    @Override
    protected List<Dataset> parseHttpResponseBody(String body) throws ParserException {
        return RequestUtils.parse(new TypeToken<List<Dataset>>() {}, body);
    }
}
