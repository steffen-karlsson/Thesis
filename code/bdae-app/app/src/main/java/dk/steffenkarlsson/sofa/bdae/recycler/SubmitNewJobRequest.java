package dk.steffenkarlsson.sofa.bdae.recycler;

import com.google.gson.annotations.SerializedName;
import com.squareup.okhttp.RequestBody;

import java.util.List;

import dk.steffenkarlsson.sofa.bdae.request.URLUtils;
import dk.steffenkarlsson.sofa.networking.ParserException;
import dk.steffenkarlsson.sofa.networking.PostRequest;

import static dk.steffenkarlsson.sofa.networking.RequestUtils.parse;

/**
 * Created by steffenkarlsson on 6/5/16.
 */
public class SubmitNewJobRequest extends PostRequest<Object> {

    private final NewJobObject mNewJob;

    public SubmitNewJobRequest(NewJobObject newJob) {
        super(URLUtils.getSubmitNewJobsUrl());

        this.mNewJob = newJob;
    }

    @Override
    protected RequestBody getData() {
        String data = parse(mNewJob);
        return RequestBody.create(json, data);
    }

    @Override
    protected Object parseHttpResponseBody(String body) throws ParserException {
        return null;
    }

    public static class NewJobObject {

        @SerializedName("dataset_name")
        protected String mDatasetName;

        @SerializedName("operation_name")
        protected String mOperationName;

        @SerializedName("query")
        protected List<String> mQuery;

        public NewJobObject(String datasetName, String operationName, List<String> query) {
            this.mDatasetName = datasetName;
            this.mOperationName = operationName;
            this.mQuery = query;
        }
    }
}
