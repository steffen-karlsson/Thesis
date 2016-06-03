package dk.steffenkarlsson.sofa.bdae.request;

import com.google.gson.reflect.TypeToken;

import java.util.List;

import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.entity.Job;
import dk.steffenkarlsson.sofa.networking.GetRequest;
import dk.steffenkarlsson.sofa.networking.ParserException;
import dk.steffenkarlsson.sofa.networking.RequestUtils;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class GetSubmittedJobsRequest extends GetRequest<List<Job>> {

    public GetSubmittedJobsRequest() {
        super(URLUtils.getSubmittedJobsUrl());
    }

    @Override
    protected List<Job> parseHttpResponseBody(String body) throws ParserException {
        return RequestUtils.parse(new TypeToken<List<Job>>() {}, body);
    }
}
